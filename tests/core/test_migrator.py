import uuid
from pathlib import Path
from typing import Optional, Dict, Any, Text, List
from unittest.mock import Mock

import pytest
from _pytest.logging import LogCaptureFixture

import rasa.utils.io as io_utils
from rasa.core.trackers import DialogueStateTracker
from rasa.exceptions import (
    NoConversationsInTrackerStore,
    NoEventsToMigrate,
    NoEventsInTimeRange,
    PublishingError,
)
from tests.conftest import MockMigrator, random_user_uttered_event


def _write_endpoint_config_to_yaml(path: Path, data: Dict[Text, Any]) -> Path:
    endpoints_path = path / "endpoints.yml"

    # write endpoints config to file
    io_utils.write_yaml_file(
        data, endpoints_path,
    )
    return endpoints_path


@pytest.mark.parametrize(
    "requested_ids,available_ids,expected",
    [(["1"], ["1"], ["1"]), (["1", "2"], ["2"], ["2"]), (None, ["2"], ["2"])],
)
def test_get_conversation_ids_to_process(
    requested_ids: Optional[List[Text]],
    available_ids: Optional[List[Text]],
    expected: Optional[List[Text]],
):
    # create and mock tracker store containing `available_ids` as keys
    tracker_store = Mock()
    tracker_store.keys.return_value = available_ids

    migrator = MockMigrator(tracker_store)
    migrator.requested_conversation_ids = requested_ids

    # noinspection PyProtectedMember
    assert migrator.get_conversation_ids_to_process() == set(expected)


@pytest.mark.parametrize(
    "requested_ids,available_ids,exception",
    [
        (["1"], [], NoConversationsInTrackerStore),  # no IDs in tracker store
        (None, [], NoConversationsInTrackerStore),  # without requested IDs
        (
            ["1", "2", "3"],
            ["4", "5", "6"],
            NoEventsToMigrate,
        ),  # no overlap between requested IDs and those available
    ],
)
def test_get_conversation_ids_to_process_error(
    requested_ids: Optional[List[Text]], available_ids: List[Text], exception: Exception
):
    # create and mock tracker store containing `available_ids` as keys
    tracker_store = Mock()
    tracker_store.keys.return_value = available_ids

    migrator = MockMigrator(tracker_store)
    migrator.requested_conversation_ids = requested_ids

    with pytest.raises(exception):
        # noinspection PyProtectedMember
        migrator.get_conversation_ids_to_process()


# noinspection PyProtectedMember
def test_fetch_events_within_time_range():
    conversation_ids = ["some-id", "another-id"]

    # prepare events from different senders and different timestamps
    event_1 = random_user_uttered_event(3)
    event_2 = random_user_uttered_event(2)
    event_3 = random_user_uttered_event(1)
    events = {
        conversation_ids[0]: [event_1, event_2],
        conversation_ids[1]: [event_3],
    }

    def _get_tracker(conversation_id: Text) -> DialogueStateTracker:
        return DialogueStateTracker.from_events(
            conversation_id, events[conversation_id]
        )

    # create mock tracker store
    tracker_store = Mock()
    tracker_store.retrieve.side_effect = _get_tracker
    tracker_store.keys.return_value = conversation_ids

    migrator = MockMigrator(tracker_store)
    migrator.requested_conversation_ids = conversation_ids

    fetched_events = migrator._fetch_events_within_time_range()

    # events should come back for all requested conversation IDs
    assert all(
        any(_id in event["sender_id"] for event in fetched_events)
        for _id in conversation_ids
    )

    # events are sorted by timestamp despite the initially different order
    assert fetched_events == list(sorted(fetched_events, key=lambda e: e["timestamp"]))


def test_fetch_events_within_time_range_tracker_does_not_err():
    # create mock tracker store that returns `None` on `retrieve()`
    tracker_store = Mock()
    tracker_store.retrieve.return_value = None
    tracker_store.keys.return_value = [uuid.uuid4()]

    migrator = MockMigrator(tracker_store)

    # no events means `NoEventsInTimeRange`
    with pytest.raises(NoEventsInTimeRange):
        # noinspection PyProtectedMember
        migrator._fetch_events_within_time_range()


def test_fetch_events_within_time_range_tracker_contains_no_events():
    # create mock tracker store that returns `None` on `retrieve()`
    tracker_store = Mock()
    tracker_store.retrieve.return_value = DialogueStateTracker.from_events(
        "a great ID", []
    )
    tracker_store.keys.return_value = ["a great ID"]

    migrator = MockMigrator(tracker_store)

    # no events means `NoEventsInTimeRange`
    with pytest.raises(NoEventsInTimeRange):
        # noinspection PyProtectedMember
        migrator._fetch_events_within_time_range()


# noinspection PyProtectedMember
def test_sort_and_select_events_by_timestamp():
    events = [
        event.as_dict()
        for event in [
            random_user_uttered_event(3),
            random_user_uttered_event(2),
            random_user_uttered_event(1),
        ]
    ]

    tracker_store = Mock()
    migrator = MockMigrator(tracker_store)

    selected_events = migrator._sort_and_select_events_by_timestamp(events)

    # events are sorted
    assert selected_events == list(
        sorted(selected_events, key=lambda e: e["timestamp"])
    )

    # apply minimum timestamp requirement, expect to get only two events back
    migrator.minimum_timestamp = 2.0
    assert migrator._sort_and_select_events_by_timestamp(events) == [
        events[1],
        events[0],
    ]
    migrator.minimum_timestamp = None

    # apply maximum timestamp requirement, expect to get only one
    migrator.maximum_timestamp = 1.1
    assert migrator._sort_and_select_events_by_timestamp(events) == [events[2]]

    # apply both requirements, get one event back
    migrator.minimum_timestamp = 2.0
    migrator.maximum_timestamp = 2.1
    assert migrator._sort_and_select_events_by_timestamp(events) == [events[1]]


# noinspection PyProtectedMember
def test_sort_and_select_events_by_timestamp_error():
    tracker_store = Mock()
    migrator = MockMigrator(tracker_store)

    # no events given
    with pytest.raises(NoEventsInTimeRange):
        migrator._sort_and_select_events_by_timestamp([])

    # supply list of events, apply timestamp constraint and no events survive
    migrator.minimum_timestamp = 3.1
    events = [random_user_uttered_event(3).as_dict()]
    with pytest.raises(NoEventsInTimeRange):
        migrator._sort_and_select_events_by_timestamp(events)


def _add_conversation_id_to_event(event: Dict, conversation_id: Text):
    event["sender_id"] = conversation_id


def test_publishing_error(caplog: LogCaptureFixture):
    # mock event broker so it raises on `publish()`
    event_broker = Mock()
    event_broker.publish.side_effect = ValueError()

    migrator = MockMigrator(event_broker=event_broker)

    user_event = random_user_uttered_event(1).as_dict()
    user_event["sender_id"] = uuid.uuid4().hex

    # noinspection PyProtectedMember
    migrator._fetch_events_within_time_range = Mock(return_value=[user_event])

    # run the export function
    with pytest.raises(PublishingError):
        # noinspection PyProtectedMember
        migrator.publish_events()
