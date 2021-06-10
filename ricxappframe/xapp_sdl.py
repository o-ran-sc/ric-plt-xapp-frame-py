# ==================================================================================
#       Copyright (c) 2020 Nokia
#       Copyright (c) 2020 AT&T Intellectual Property.
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
sdl functionality
"""

import msgpack
from ricsdl.syncstorage import SyncStorage


class SDLWrapper:
    """
    Provides convenient wrapper methods for using the SDL Python interface.
    Optionally uses msgpack for binary (de)serialization:
    see https://msgpack.org/index.html

    Published as a standalone module (and kept separate from the Xapp
    framework classes) so these features can be used outside Xapps.
    """

    def __init__(self, use_fake_sdl=False):
        """
        init

        Parameters
        ----------
        use_fake_sdl: bool (optional, default False)
            if this is True, then use SDL's in-memory backend,
            which is very useful for testing since it allows use
            of SDL without a running SDL or Redis instance.
            This can be used while developing an xapp and also
            for monkeypatching during unit testing; e.g., the xapp
            framework unit tests do this.
        """
        if use_fake_sdl:
            self._sdl = SyncStorage(fake_db_backend="dict")
        else:
            self._sdl = SyncStorage()

    def set(self, ns, key, value, usemsgpack=True):
        """
        Stores a key-value pair,
        optionally serializing the value to bytes using msgpack.

        TODO: discuss whether usemsgpack should *default* to True or
        False here. This seems like a usage statistic question (that we
        don't have enough data for yet). Are more uses for an xapp to
        write/read their own data, or will more xapps end up reading data
        written by some other thing? I think it's too early to know.

        Parameters
        ----------
        ns: string
            SDL namespace
        key: string
            SDL key
        value:
            Object or byte array to store.  See the `usemsgpack` parameter.
        usemsgpack: boolean (optional, default is True)
            Determines whether the value is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the value to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the value can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the value must be bytes.
        """
        if usemsgpack:
            value = msgpack.packb(value, use_bin_type=True)
        self._sdl.set(ns, {key: value})

    def set_if(self, ns, key, old_value, new_value, usemsgpack=True):
        """
        Conditionally modify the value of a key if the current value in data storage matches the
        user's last known value.

        Parameters
        ----------
        ns: string
            SDL namespace
        key: string
            SDL key
        old_value:
            Lask known object or byte array.  See the `usemsgpack` parameter.
        new_value:
            Object or byte array to be written.  See the `usemsgpack` parameter.
        usemsgpack: boolean (optional, default is True)
            Determines whether the value is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the value to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the value can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the value must be bytes.

        Returns
        -------
        bool
            True for successful modification, false if the user's last known data did not
            match the current value in data storage.
        """
        if usemsgpack:
            old_value = msgpack.packb(old_value, use_bin_type=True)
            new_value = msgpack.packb(new_value, use_bin_type=True)
        return self._sdl.set_if(ns, key, old_value, new_value)

    def set_if_not_exists(self, ns, key, value, usemsgpack=True):
        """
        Write data to SDL storage if key does not exist.

        Parameters
        ----------
        ns: string
            SDL namespace
        key: string
            SDL key
        value:
            Object or byte array to store.  See the `usemsgpack` parameter.
        usemsgpack: boolean (optional, default is True)
            Determines whether the value is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the value to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the value can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the value must be bytes.

        Returns
        -------
        bool
            True for successful modification, false if the user's last known data did not
            match the current value in data storage.
        """
        if usemsgpack:
            value = msgpack.packb(value, use_bin_type=True)
        return self._sdl.set_if_not_exists(ns, key, value)

    def get(self, ns, key, usemsgpack=True):
        """
        Gets the value for the specified namespace and key,
        optionally deserializing stored bytes using msgpack.

        Parameters
        ----------
        ns: string
            SDL namespace
        key: string
            SDL key
        usemsgpack: boolean (optional, default is True)
            If usemsgpack is True, the byte array stored by SDL is deserialized
            using msgpack to yield the original object that was stored.
            If usemsgpack is False, the byte array stored by SDL is returned
            without further processing.

        Returns
        -------
        Value
            See the usemsgpack parameter for an explanation of the returned value type.
            Answers None if the key is not found.
        """
        result = None
        ret_dict = self._sdl.get(ns, {key})
        if key in ret_dict:
            result = ret_dict[key]
            if usemsgpack:
                result = msgpack.unpackb(result, raw=False)
        return result

    def find_keys(self, ns, prefix):
        """
        Find all keys matching search pattern under the namespace.

        Parameters
        ----------
        ns: string
            SDL namespace
        prefix: string
            Key search pattern

        Returns
        -------
        keys: list
            A list of found keys.
        """
        return self._sdl.find_keys(ns, f"{prefix}*")

    def find_and_get(self, ns, prefix, usemsgpack=True):
        """
        Gets all key-value pairs in the specified namespace
        with keys that start with the specified prefix,
        optionally deserializing stored bytes using msgpack.

        Parameters
        ----------
        ns: string
           SDL namespace
        prefix: string
            the key prefix
        usemsgpack: boolean (optional, default is True)
            If usemsgpack is True, every byte array stored by SDL is deserialized
            using msgpack to yield the original value that was stored.
            If usemsgpack is False, every byte array stored by SDL is returned
            without further processing.

        Returns
        -------
        Dictionary of key-value pairs
            Each key has the specified prefix.
            See the usemsgpack parameter for an explanation of the returned value types.
            Answers an empty dictionary if no keys matched the prefix.
        """

        # note: SDL "*" usage is inconsistent with real python regex, where it would be ".*"
        ret_dict = self._sdl.find_and_get(ns, f"{prefix}*")
        if usemsgpack:
            ret_dict = {k: msgpack.unpackb(v, raw=False) for k, v in ret_dict.items()}
        return ret_dict

    def delete(self, ns, key):
        """
        Deletes the key-value pair with the specified key in the specified namespace.

        Parameters
        ----------
        ns: string
           SDL namespace
        key: string
            SDL key
        """
        self._sdl.remove(ns, {key})

    def delete_if(self, ns, key, value, usemsgpack=True):
        """
        Conditionally remove data from SDL storage if the current data value matches the user's
        last known value.

        Parameters
        ----------
        ns: string
            SDL namespace
        key: string
            SDL key
        value:
            Object or byte array to store.  See the `usemsgpack` parameter.
        usemsgpack: boolean (optional, default is True)
            Determines whether the value is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the value to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the value can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the value must be bytes.

        Returns
        -------
        bool
            True if successful removal, false if the user's last known data did not match the
            current value in data storage.
        """
        if usemsgpack:
            value = msgpack.packb(value, use_bin_type=True)
        return self._sdl.remove_if(ns, key, value)

    def add_member(self, ns, group, member, usemsgpack=True):
        """
        Add new members to a SDL group under the namespace.

        Parameters
        ----------
        ns: string
            SDL namespace
        group: string
            group name
        member:
            member to be added
        usemsgpack: boolean (optional, default is True)
            Determines whether the member is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the member to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the member can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the member must be bytes.
        """
        if usemsgpack:
            member = msgpack.packb(member, use_bin_type=True)
        self._sdl.add_member(ns, group, {member})

    def remove_member(self, ns, group, member, usemsgpack=True):
        """
        Remove members from a SDL group.

        Parameters
        ----------
        ns: string
            SDL namespace
        group: string
            group name
        member:
            member to be removed
        usemsgpack: boolean (optional, default is True)
            Determines whether the member is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the member to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the member can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the member must be bytes.
        """
        if usemsgpack:
            member = msgpack.packb(member, use_bin_type=True)
        self._sdl.remove_member(ns, group, {member})

    def remove_group(self, ns, group):
        """
        Remove a SDL group along with its members.

        Parameters
        ----------
        ns: string
            SDL namespace
        group: string
            group name to remove
        usemsgpack: boolean (optional, default is True)
            Determines whether the member is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the member to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the member can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the member must be bytes.
        """
        self._sdl.remove_group(ns, group)

    def get_members(self, ns, group, usemsgpack=True):
        """
        Get all the members of a SDL group.

        Parameters
        ----------
        ns: string
            SDL namespace
        group: string
            group name to retrive
        usemsgpack: boolean (optional, default is True)
            Determines whether the member is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the member to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the member can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the member must be bytes.

        Returns
        -------
        Set[str] or Set[bytes]
            A set of the members of the group.
        None
        """
        ret_set = self._sdl.get_members(ns, group)
        if usemsgpack:
            ret_set = {msgpack.unpackb(m, raw=False) for m in ret_set}
        return ret_set

    def is_member(self, ns, group, member, usemsgpack=True):
        """
        Validate if a given member is in the SDL group.

        Parameters
        ----------
        ns: string
            SDL namespace
        group: string
            group name
        member:
            member to validate
        usemsgpack: boolean (optional, default is True)
            Determines whether the member is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the member to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the member can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the member must be bytes.

        Returns
        -------
        bool
            True if member was in the group, false otherwise.
        """
        if usemsgpack:
            member = msgpack.packb(member, use_bin_type=True)
        return self._sdl.is_member(ns, group, member)

    def group_size(self, ns, group):
        """
        Return the number of members in a group.
        If the group does not exist, value 0 is returned.

        Parameters
        ----------
        ns: string
            SDL namespace
        group: string
            group name to retrive size
        usemsgpack: boolean (optional, default is True)
            Determines whether the member is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the member to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the member can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the member must be bytes.

        Returns
        -------
        int
            Number of members in a group.
        """
        return self._sdl.group_size(ns, group)

    def set_and_publish(self, ns, channel, event, key, value, usemsgpack=True):
        """
        Publish event to channel after writing data.

        Parameters
        ----------
        ns: string
            SDL namespace
        channel: string
            channel to publish event
        event: string
            published message
        key: string
            SDL key
        value:
            Object or byte array to store.  See the `usemsgpack` parameter.
        usemsgpack: boolean (optional, default is True)
            Determines whether the value is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the value to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the value can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the value must be bytes.
        """
        if usemsgpack:
            value = msgpack.packb(value, use_bin_type=True)
        self._sdl.set_and_publish(ns, {channel: event}, {key: value})

    def set_if_and_publish(self, ns, channel, event, key, old_value, new_value, usemsgpack=True):
        """
        Publish event to channel after conditionally modifying the value of a key if the
        current value in data storage matches the user's last known value.

        Parameters
        ----------
        ns: string
            SDL namespace
        channel: string
            channel to publish event
        event: string
            published message
        key: string
            SDL key
        old_value:
            Lask known object or byte array.  See the `usemsgpack` parameter.
        new_value:
            Object or byte array to be written.  See the `usemsgpack` parameter.
        usemsgpack: boolean (optional, default is True)
            Determines whether the old_value & new_value is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the old_value & new_value to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the old_value & new_value can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the old_value & new_value must be bytes.

        Returns
        -------
        bool
            True for successful modification, false if the user's last known data did not
            match the current value in data storage.
        """
        if usemsgpack:
            old_value = msgpack.packb(old_value, use_bin_type=True)
            new_value = msgpack.packb(new_value, use_bin_type=True)
        return self._sdl.set_if_and_publish(ns, {channel: event}, key, old_value, new_value)

    def set_if_not_exists_and_publish(self, ns, channel, event, key, value, usemsgpack=True):
        """
        Publish event to channel after writing data to SDL storage if key does not exist.

        Parameters
        ----------
        ns: string
            SDL namespace
        channel: string
            channel to publish event
        event: string
            published message
        key: string
            SDL key
        value:
            Object or byte array to store.  See the `usemsgpack` parameter.
        usemsgpack: boolean (optional, default is True)
            Determines whether the value is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the value to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the value can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the value must be bytes.

        Returns
        -------
        bool
            True if key didn't exist yet and set operation was executed, false if key already
            existed and thus its value was left untouched.
        """
        if usemsgpack:
            value = msgpack.packb(value, use_bin_type=True)
        return self._sdl.set_if_not_exists_and_publish(ns, {channel: event}, key, value)

    def remove_and_publish(self, ns, channel, event, key):
        """
        Publish event to channel after removing data.

        Parameters
        ----------
        ns: string
            SDL namespace
        channel: string
            channel to publish event
        event: string
            published message
        key: string
            SDL key
        """
        self._sdl.remove_and_publish(ns, {channel: event}, {key})

    def remove_if_and_publish(self, ns, channel, event, key, value, usemsgpack=True):
        """
        Publish event to channel after removing key and its data from database if the
        current data value is expected one.

        Parameters
        ----------
        ns: string
            SDL namespace
        channel: string
            channel to publish event
        event: string
            published message
        key: string
            SDL key
        value:
            Object or byte array to store.  See the `usemsgpack` parameter.
        usemsgpack: boolean (optional, default is True)
            Determines whether the value is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the value to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the value can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the value must be bytes.

        Returns
        -------
        bool
            True if successful removal, false if the user's last known data did not match the
            current value in data storage.
        """
        if usemsgpack:
            value = msgpack.packb(value, use_bin_type=True)
        return self._sdl.remove_if_and_publish(ns, {channel: event}, key, value)

    def remove_all_and_publish(self, ns, channel, event):
        """
        Publish event to channel after removing all keys under the namespace.

        Parameters
        ----------
        ns: string
            SDL namespace
        channel: string
            channel to publish event
        event: string
            published message
        """
        self._sdl.remove_all_and_publish(ns, {channel: event})

    def subscribe_channel(self, ns, cb, channel):
        """
        Subscribes the client to the specified channels.

        Parameters
        ----------
        ns: string
            SDL namespace
        cb:
            A function that is called when an event on channel is received.
        channel: string
            channel to subscribe
        """
        self._sdl.subscribe_channel(ns, cb, {channel})

    def unsubscribe_channel(self, ns, channel):
        """
        unsubscribe_channel removes subscription from one or several channels.

        Parameters
        ----------
        ns: string
            SDL namespace
        channel: string
            channel to unsubscribe
        """
        self._sdl.unsubscribe_channel(ns, {channel})

    def start_event_listener(self):
        """
        start_event_listener creates an event loop in a separate thread for handling
        events from subscriptions. The registered callback function will be called
        when an event is received.
        """
        self._sdl.start_event_listener()

    def handle_events(self):
        """
        handle_events is a non-blocking function that returns a tuple containing channel
        name and a list of message(s) received from an event. The registered callback
        function will still be called when an event is received.

        This function is called if SDL user decides to handle notifications in its own
        event loop. Calling this function after start_event_listener raises an exception.
        If there are no notifications, these returns None.

        Returns
        -------
        Tuple:
            (channel: str, messages: list of str)
        """
        return self._sdl.handle_events()

    def healthcheck(self):
        """
        Checks if the sdl connection is healthy.

        Returns
        -------
        bool
        """
        return self._sdl.is_active()
