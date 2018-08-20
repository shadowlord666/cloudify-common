from cloudify_rest_client.responses import ListResponse


class Operation(dict):
    def __init__(self, operation):
        self.update(operation)

    @property
    def id(self):
        return self.get('id')

    @property
    def execution(self):
        return self.get('execution_id')

    @property
    def state(self):
        return self.get('state')

    @property
    def created_at(self):
        return self.get('created_at')


class OperationsClient(object):
    def __init__(self, api):
        self.api = api
        self._uri_prefix = 'operations'
        self._wrapper_cls = Operation

    def list(self, execution_id):
        params = {'execution_id': execution_id}
        response = self.api.get('/{self._uri_prefix}'.format(self=self),
                                params=params)
        return ListResponse(
            [self._wrapper_cls(item) for item in response['items']],
            response['metadata'])

    def create(self, operation_id, name, execution_id):
        params = {
            'name': name,
            'execution_id': execution_id
        }
        uri = '/operations/{0}'.format(operation_id)
        response = self.api.put(uri, data=params, expected_status_code=201)
        return Operation(response)

    def update(self, operation_id, state):
        uri = '/operations/{0}'.format(operation_id)
        response = self.api.patch(uri, data={'state': state})
        return Operation(response)
