from rest_framework.renderers import JSONRenderer


class PublicRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context['response']
        request = renderer_context['request']
        success = response.status_code < 400

        response_data = {
            'code': response.status_code,
            'msg': 'ok' if success else 'error',
            'data': data,
        }
        return super().render(response_data, accepted_media_type, renderer_context)