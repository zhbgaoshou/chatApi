import json
from datetime import datetime

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.http import StreamingHttpResponse
from openai import OpenAI
from chat.models import Room, Message
from chat.serializers import RoomSerializer, MessageSerializer
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(
    api_key=os.getenv("API_KEY"),
    organization=os.getenv("ORGANIZATION"),
    project=os.getenv("PROJECT"),
)


# Create your views here.
class ChatView(GenericAPIView):
    def post(self, request):
        # 获取相关参数
        data = json.loads(request.body)
        model = request.query_params.get('model')
        content = data['content']
        room = data['room']
        user = request.user
        fetch_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # api需要的参数
        messages_list = Message.objects.filter(room=room)[:50]
        serializer_message_list = MessageSerializer(messages_list, many=True)
        message_params = serializer_message_list.data + [{'role': 'user', 'content': content}]

        #
        messages = [{"role": "system", "content": "You are a helpful assistant."}] + message_params
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )

        def event_stream():
            ai_content = ''
            try:
                for chunk in completion:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        ai_content += delta.content
                    yield delta.content
            except Exception as e:
                yield f"data: Error: {str(e)}"
            finally:
                if ai_content != '':
                    # 存当前的上下文
                    res_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    message_dict = {"role": 'user', "content": content, "room": room, "user": user.id, "model": model,
                                    'date_time': fetch_time}
                    ai_message_dict = {"role": 'assistant', "content": ai_content, "room": room, "user": user.id,
                                       "model": model, 'date_time': res_time}
                    cxt_list = [message_dict, ai_message_dict]
                    message_serializer = MessageSerializer(data=cxt_list, many=True)
                    if message_serializer.is_valid():
                        message_serializer.save()
                    else:
                        print(message_serializer.errors)
                        return Response(message_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'

        return response


class RoomView(ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    filterset_fields = ['user']
    search_fields = ['name']
    ordering_fields = ['user__username', 'id']  # 允许排序的字段
    ordering = ['id']


class MessageView(ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    filterset_fields = ['user', 'room']  # 过滤字段
    search_fields = ['content']  # 搜索字段
    ordering_fields = ['user__username', 'id']  # 允许排序的字段
    ordering = ['id']  # 默认排序
