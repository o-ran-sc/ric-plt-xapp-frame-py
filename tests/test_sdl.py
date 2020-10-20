# ==================================================================================
#       Copyright (c) 2019-2020 Nokia
#       Copyright (c) 2018-2020 AT&T Intellectual Property.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# ==================================================================================
"""
tests data functions
"""
import time
from ricxappframe.xapp_sdl import SDLWrapper


NS = "testns"


def test_sdl():
    """
    test raw sdl functions
    """
    sdl = SDLWrapper(use_fake_sdl=True)
    sdl.set(NS, "as.df1", "data")
    sdl.set(NS, "as.df2", "data2")
    assert sdl.get(NS, "as.df1") == "data"
    assert sdl.get(NS, "as.df2") == "data2"
    assert sdl.find_and_get(NS, "as.df1") == {"as.df1": "data"}
    assert sdl.find_and_get(NS, "as.df2") == {"as.df2": "data2"}
    assert sdl.find_and_get(NS, "as.df") == {"as.df1": "data", "as.df2": "data2"}
    assert sdl.find_and_get(NS, "as.d") == {"as.df1": "data", "as.df2": "data2"}
    assert sdl.find_and_get(NS, "as.") == {"as.df1": "data", "as.df2": "data2"}
    assert sdl.find_and_get(NS, "asd") == {}

    # delete 1
    sdl.delete(NS, "as.df1")
    assert sdl.get(NS, "as.df1") is None
    assert sdl.get(NS, "as.df2") == "data2"

    # delete 2
    sdl.delete(NS, "as.df2")
    assert sdl.get(NS, "as.df2") is None

    assert sdl.find_and_get(NS, "as.df") == {}
    assert sdl.find_and_get(NS, "") == {}


def test_sdl_set_get():
    """
    test set, get realted sdl methods
    """
    sdl = SDLWrapper(use_fake_sdl=True)

    # set_if
    sdl.set(NS, "gs.df1", "old")
    assert sdl.get(NS, "gs.df1") == "old"

    sdl.set_if(NS, "gs.df1", "young", "new")
    assert sdl.get(NS, "gs.df1") == "old"

    sdl.set_if(NS, "gs.df1", "old", "new")
    assert sdl.get(NS, "gs.df1") == "new"

    # set_if_not_exists
    sdl.set(NS, "gs.df2", "old")
    assert sdl.get(NS, "gs.df2") == "old"

    sdl.set_if_not_exists(NS, "gs.df2", "new")
    assert sdl.get(NS, "gs.df2") == "old"

    sdl.set_if_not_exists(NS, "gs.df3", "new")
    assert sdl.get(NS, "gs.df3") == "new"

    # find_keys
    assert sdl.find_keys(NS, "gs") == ["gs.df1", "gs.df2", "gs.df3"]
    assert sdl.find_keys(NS, "gs.df1") == ["gs.df1"]
    assert sdl.find_keys(NS, "gs.df2") == ["gs.df2"]
    assert sdl.find_keys(NS, "gs.df3") == ["gs.df3"]

    # delete_if
    sdl.set(NS, "gs.df4", "delete_this")

    assert sdl.delete_if(NS, "gs.df4", "delete") is False
    assert sdl.delete_if(NS, "gs.df4", "delete_this") is True
    assert sdl.get(NS, "gs.df4") is None


def test_sdl_member():
    """
    test member related sdl methods
    """
    # add_member, remove_member, get_members
    sdl = SDLWrapper(use_fake_sdl=True)

    sdl.add_member(NS, "group1", "member1")
    assert sdl.is_member(NS, "group1", "member1") is True

    sdl.remove_member(NS, "group1", "not_member")
    assert sdl.is_member(NS, "group1", "member1") is True

    sdl.remove_member(NS, "group1", "member1")
    assert sdl.is_member(NS, "group1", "member1") is False

    # remove_group, group_size
    sdl.add_member(NS, "group2", "member1")
    sdl.add_member(NS, "group2", "member2")
    assert sdl.group_size(NS, "group2") == 2
    sdl.remove_group(NS, "group2")
    assert sdl.group_size(NS, "group2") == 0

    # get_members
    sdl.add_member(NS, "group3", "member1")
    sdl.add_member(NS, "group3", "member2")
    members = sdl.get_members(NS, "group3")
    assert "member1" in members
    assert "member2" in members


def test_sdl_set_and_publish_with_handle_events():
    """
    test set_and_publish* related sdl methods
    """
    CH = "channel"
    EVENT = "event"
    CALLED = None

    def cb(channel, event):
        nonlocal CH
        nonlocal EVENT
        nonlocal CALLED
        # test is cb called
        CALLED = True
        assert channel == CH
        assert event == EVENT

    sdl = SDLWrapper(use_fake_sdl=True)
    sdl.subscribe_channel(NS, cb, "channel")

    # set_and_publish
    CALLED = False
    sdl.set_and_publish(NS, "channel", "event", "nt.df1", "old")
    sdl.handle_events()
    assert sdl.get(NS, "nt.df1") == "old"
    assert CALLED is True

    # set_if_and_publish fail
    CALLED = False
    sdl.set_if_and_publish(NS, "channel", "event", "nt.df1", "young", "new")
    sdl.handle_events()
    assert sdl.get(NS, "nt.df1") == "old"
    assert CALLED is False
    # set_if_and_publish success
    sdl.set_if_and_publish(NS, "channel", "event", "nt.df1", "old", "new")
    sdl.handle_events()
    assert sdl.get(NS, "nt.df1") == "new"
    assert CALLED is True

    # set_if_not_exists_and_publish fail
    CALLED = False
    sdl.set_if_not_exists_and_publish(NS, "channel", "event", "nt.df1", "latest")
    sdl.handle_events()
    assert sdl.get(NS, "nt.df1") == "new"
    assert CALLED is False
    # set_if_not_exists_and_publish success
    sdl.set_if_not_exists_and_publish(
        NS, "channel", "event", "nt.df2", "latest")
    sdl.handle_events()
    assert sdl.get(NS, "nt.df2") == "latest"
    assert CALLED is True

    sdl.unsubscribe_channel(NS, "channel")


def test_sdl_remove_and_publish_with_start_event_listener():
    """
    test remove_and_publish* related sdl methods
    """
    CH = "channel"
    EVENT = "event"
    CALLED = None

    def cb(channel, event):
        nonlocal CH
        nonlocal EVENT
        nonlocal CALLED
        CALLED = True
        assert channel == CH
        assert event == EVENT

    sdl = SDLWrapper(use_fake_sdl=True)
    sdl.subscribe_channel(NS, cb, "channel")
    sdl.start_event_listener()

    # remove_and_publish success
    CALLED = False
    sdl.set(NS, "nt.df1", "old")
    sdl.remove_and_publish(NS, "channel", "event", "nt.df1")
    time.sleep(0.3)
    assert sdl.get(NS, "nt.df1") is None
    assert CALLED is True

    # remove_if_and_publish
    CALLED = False
    sdl.set(NS, "nt.df1", "old")
    # fail
    sdl.remove_if_and_publish(NS, "channel", "event", "nt.df1", "new")
    time.sleep(0.3)
    assert sdl.get(NS, "nt.df1") == "old"
    assert CALLED is False
    # success
    sdl.remove_if_and_publish(NS, "channel", "event", "nt.df1", "old")
    time.sleep(0.3)
    assert sdl.get(NS, "nt.df1") is None
    assert CALLED is True

    # remove_all_and_publish
    CALLED = False
    sdl.set(NS, "nt.df1", "data1")
    sdl.set(NS, "nt.df2", "data2")
    sdl.set(NS, "nt.df3", "data3")
    sdl.remove_all_and_publish(NS, "channel", "event")
    time.sleep(0.3)
    assert sdl.get(NS, "nt.df1") is None
    assert sdl.get(NS, "nt.df2") is None
    assert sdl.get(NS, "nt.df3") is None
    assert sdl.find_keys(NS, "*") == []
    assert CALLED is True

    sdl.unsubscribe_channel(NS, "channel")
