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
    This is a wrapper around the SDL Python interface.

    We do not embed the below directly in the Xapp classes because
    this SDL wrapper is useful for other python apps, for example A1
    Mediator uses this verbatim. Therefore, we leave this here as a
    seperate instantiable object so it can be used outside of xapps
    too.  One could argue this get moved into *sdl itself*.

    We currently use msgpack for binary (de)serialization:
    https://msgpack.org/index.html
    """

    def __init__(self, use_fake_sdl=False):
        """
        init

        Parameters
        ----------
        use_fake_sdl: bool
            if this is True (default: False), then SDLs "fake dict
            backend" is used, which is very useful for testing since
            it allows you to use SDL without any SDL or Redis deployed at
            all. This can be used while developing your xapp, and also
            for monkeypatching during unit testing (e.g., the xapp
            framework unit tests do this).
        """
        if use_fake_sdl:
            self._sdl = SyncStorage(fake_db_backend="dict")
        else:
            self._sdl = SyncStorage()

    def set(self, ns, key, value, usemsgpack=True):
        """
        sets a key

        TODO: discuss whether usemsgpack should *default* to True or
        False here. This seems like a usage statistic question (that we
        don't have enough data for yet). Are more uses for an xapp to
        write/read their own data, or will more xapps end up reading data
        written by some other thing? I think it's too early to know
        this. So we go with True as the very first user of this, a1, does
        this. I'm open to changing this default to False later with
        evidence.

        Parameters
        ----------
        ns: string
        the sdl namespace
        key: string
        the sdl key
        value:
        if usemsgpack is True, value can be anything serializable by msgpack
        if usemsgpack is False, value must be bytes
        usemsgpack: boolean (optional)
        determines whether the value is serialized using msgpack
        """
        if usemsgpack:
            self._sdl.set(ns, {key: msgpack.packb(value, use_bin_type=True)})
        else:
            self._sdl.set(ns, {key: value})

    def get(self, ns, key, usemsgpack=True):
        """
        get a key

        Parameters
        ----------
        ns: string
           the sdl namespace
        key: string
            the sdl key
        usemsgpack: boolean (optional)
            if usemsgpack is True, the value is deserialized using msgpack
            if usemsgpack is False, the value is returned as raw bytes

        Returns
        -------
        None (if not exist) or see above; depends on usemsgpack
        """
        ret_dict = self._sdl.get(ns, {key})
        if key in ret_dict:
            if usemsgpack:
                return msgpack.unpackb(ret_dict[key], raw=False)
            return ret_dict[key]

        return None

    def find_and_get(self, ns, prefix, usemsgpack=True):
        """
        get all k v pairs that start with prefix

        Parameters
        ----------
        ns: string
           the sdl namespace
        key: string
            the sdl key
        prefix: string
            the prefix
        usemsgpack: boolean (optional)
            if usemsgpack is True, the value returned is a dict where each value has been deserialized using msgpack
            if usemsgpack is False, the value returned is as a dict mapping keys to raw bytes

        Returns
        -------
        {} (if no keys match) or see above; depends on usemsgpack
        """

        # note: SDL "*" usage is inconsistent with real python regex, where it would be ".*"
        ret_dict = self._sdl.find_and_get(ns, "{0}*".format(prefix))
        if usemsgpack:
            return {k: msgpack.unpackb(v, raw=False) for k, v in ret_dict.items()}
        return ret_dict

    def delete(self, ns, key):
        """
        delete a key

        Parameters
        ----------
        ns: string
           the sdl namespace
        key: string
            the sdl key
        """
        self._sdl.remove(ns, {key})

    def healthcheck(self):
        """
        checks if the sdl connection is healthy

        Returns
        -------
        bool
        """
        return self._sdl.is_active()
