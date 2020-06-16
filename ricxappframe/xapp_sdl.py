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
        ret_dict = self._sdl.find_and_get(ns, "{0}*".format(prefix))
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

    def healthcheck(self):
        """
        Checks if the sdl connection is healthy.

        Returns
        -------
        bool
        """
        return self._sdl.is_active()
