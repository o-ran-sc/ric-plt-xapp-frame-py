#       Copyright (c) 2022 Nokia
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
#
# Subscription interface implements the subscription manager REST based interface defined in
# https://docs.o-ran-sc.org/projects/o-ran-sc-ric-plt-submgr/en/latest/user-guide.html
#

import ricxappframe.subsclient as subsclient
import ricxappframe.xapp_rest as ricrest
from mdclogpy import Logger

logging = Logger(name=__name__)


class NewSubscriber():

    def __init__(self, uri, timeout=None, local_address="0.0.0.0", local_port=8088, rmr_port=4061):
        """
        init

        Parameters
        ----------
        uri: string
            xapp submgr service uri
        timeout: int
            rest method timeout
        local_address: string
            local interface IP address for rest service binding (for response handler)
        local_port: int
            local service port nunber for rest service binding (for response handler)
        rmr_port: int
            rmr port number
        """
        self.uri = uri
        self.timeout = timeout
        self.local_address = local_address
        self.local_port = local_port
        self.rmr_port = rmr_port
        self.url = "/ric/v1/subscriptions/response"
        self.serverHandler = None
        self.responseCB = None
        # Configure API
        configuration = subsclient.Configuration()
        configuration.verify_ssl = False
        configuration.host = "http://127.0.0.1:8088/"
        self.api = subsclient.ApiClient(configuration)

    def _responsePostHandler(self, name, path, data, ctype):
        """
        _resppnsePostHandler
            internally used subscription reponse handler it the callback function is not set
        """
        return "{}", 'application/json', "OK", 200

    # following methods are wrappers to hide the swagger client
    def SubscriptionParamsClientEndpoint(self, host=None, http_port=None, rmr_port=None):
        return subsclient.SubscriptionParamsClientEndpoint(host, http_port, rmr_port)

    def SubscriptionParamsE2SubscriptionDirectives(self, e2_timeout_timer_value=None, e2_retry_count=None, rmr_routing_needed=None):
        return subsclient.SubscriptionParamsE2SubscriptionDirectives(e2_timeout_timer_value, e2_retry_count, rmr_routing_needed)

    def SubsequentAction(self, subsequent_action_type=None, time_to_wait=None):
        return subsclient.SubsequentAction(subsequent_action_type, time_to_wait)

    def ActionToBeSetup(self, action_id=None, action_type=None, action_definition=None, subsequent_action=None):
        return subsclient.ActionToBeSetup(action_id, action_type, action_definition, subsequent_action)

    def SubscriptionDetail(self, xapp_event_instance_id=None, event_triggers=None, action_to_be_setup_list=None):
        return subsclient.SubscriptionDetail(xapp_event_instance_id, event_triggers, action_to_be_setup_list)

    def SubscriptionParams(self, subscription_id=None, client_endpoint=None, meid=None, ran_function_id=None, e2_subscription_directives=None, subscription_details=None):
        return subsclient.SubscriptionParams(subscription_id, client_endpoint, meid, ran_function_id, e2_subscription_directives, subscription_details)

    def Subscribe(self, subs_params=None):
        """
        Subscribe
            subscription request

        Parameters
        ----------
        subs_params: SubscriptionParams
            structured subscription data definition defined in subsclient
        Returns
        -------
        SubscriptionResponse
             json string of SubscriptionResponse object
        """
#        if subs_params is not None and type(subs_params) is subsclient.models.subscription_params.SubscriptionParams:
        if subs_params is not None:
            response = self.api.request(method="POST", url=self.uri, headers=None, body=subs_params.to_dict())
            return response.data, response.reason, response.status
        return None, "Input parameter is not SubscriptionParams{}", 500

    def UnSubscribe(self, subs_id=None):
        """
        UnSubscribe
            subscription remove

        Parameters
        ----------
        subs_id: int
            subscription id returned in SubscriptionResponse
        Returns
        -------
        response.reason: string
            http reason
        response.status: int
            http status code
        """
        response = self.api.request(method="DELETE", url=self.uri + "/subscriptions/" + subs_id, headers=None)
        return response.data, response.reason, response.status

    def QuerySubscriptions(self):
        """
        QuerySubscriptions
            Query all subscriptions

        Returns
        -------
        response.data: json string
            SubscriptionList
        response.reason: string
            http reason
        response.status: int
            http status code
        """
        response = self.api.request(method="GET", url=self.uri + "/subscriptions", headers=None)
        return response.data, response.reason, response.status

    def ResponseHandler(self, responseCB=None, server=None):
        """
        ResponseHandler
            Starts the response handler and set the callback

        Parameters
        ----------
        responseCB
            Set the callback handler, if not set the the default self._responsePostHandler is used
        server: xapp_rest.ThreadedHTTPServer
            if set then the existing xapp_rest.ThreadedHTTPServer handler is used, otherwise a new will be created

        Returns
        -------
        status: boolean
            True = success, False = failed
        """
        # create the thread HTTP server
        self.serverHandler = server
        if self.serverHandler is None:
            # make the serverhandler
            self.serverHandler = ricrest.ThreadedHTTPServer(self.local_address, self.local_port)
            self.serverHandler.start()
        if self.serverHandler is not None:
            if responseCB is not None:
                self.responseCB = responseCB
            # get http handler with object reference
            self.serverHandler.handler.add_handler(self.serverHandler.handler, "POST", "response", self.url, responseCB)
            return True
        else:
            return False
