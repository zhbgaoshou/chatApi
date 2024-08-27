import json
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.http import StreamingHttpResponse
from openai import OpenAI
from chat.models import Room, Message
from chat.serializers import RoomSerializer, MessageSerializer
from dotenv import load_dotenv
import os

load_dotenv()
openai = OpenAI(
    api_key=os.getenv("API_KEY"),
    organization=os.getenv("ORGANIZATION"),
    project=os.getenv("PROJECT"),
)


# Create your views here.
class ChatView(APIView):
    @transaction.atomic
    def post(self, request):
        # 获取相关参数
        data = json.loads(request.body)
        model = request.query_params.get('model')
        content = data['content']
        room = data['room']
        user = request.user
        fetch_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 获取消息上下文
        serializer_message_list = self.get_messages(room)
        message_params = serializer_message_list.data + [{'role': 'user', 'content': content}]

        # 准备 OpenAI API 请求数据
        messages = [{"role": "system", "content": "You are a helpful assistant."}] + message_params
        # 发送请求
        completion = openai.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )

        response = StreamingHttpResponse(self.event_stream(completion, content, room, user, fetch_time, model),
                                         content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'

        return response

    def event_stream(self, completion, content, room, user, fetch_time, model):
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
            if ai_content:
                self.save_message(content, ai_content, room, user, model, fetch_time)

    def save_message(self, content, ai_content, room, user, model, fetch_time):
        # 存当前的上下文
        res_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 使用字典推导式创建消息字典
        common_fields = {
            "room": room,
            "user": user.id,
            "model": model,
        }
        message_dict = {**common_fields, "role": 'user', "content": content, "date_time": fetch_time}
        ai_message_dict = {**common_fields, "role": 'assistant', "content": ai_content, "date_time": res_time}
        cxt_list = [message_dict, ai_message_dict]

        message_serializer = MessageSerializer(data=cxt_list, many=True)
        if message_serializer.is_valid():
            message_serializer.save()
        else:
            print(message_serializer.errors)
            return Response(message_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_messages(self, room):
        messages_list = Message.objects.filter(room=room).order_by('id')[:20].only('role', 'content')
        serializer_message_list = MessageSerializer(messages_list, many=True)
        return serializer_message_list


class RoomView(ModelViewSet):
    queryset = Room.objects.all().order_by('-create_time')
    serializer_class = RoomSerializer
    filterset_fields = ['user']
    search_fields = ['name']
    ordering_fields = ['user__username', 'id']  # 允许排序的字段
    ordering = ['-create_time']

    @action(detail=False, methods=['get'])
    def categorized(self, request):

        user = request.query_params.get('user')
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        three_days_ago_start = today_start - timedelta(days=3)
        seven_days_ago_start = today_start - timedelta(days=7)
        one_month_ago_start = today_start - timedelta(days=30)
        today_end = today_start + timedelta(days=1)

        # 获取过滤条件范围内的所有数据
        start_time = one_month_ago_start
        end_time = today_end
        rooms = Room.objects.filter(create_time__gte=start_time, create_time__lt=end_time, user=user)
        active_room = rooms.filter(active=True)

        # 在内存中对查询结果进行分类
        today_rooms = []
        yesterday_rooms = []
        three_days_ago_rooms = []
        seven_days_ago_rooms = []
        one_month_ago_rooms = []

        for room in rooms:
            if today_start <= room.create_time < today_end:
                today_rooms.append(room)
            elif yesterday_start <= room.create_time < today_start:
                yesterday_rooms.append(room)
            elif three_days_ago_start <= room.create_time < yesterday_start:
                three_days_ago_rooms.append(room)
            elif seven_days_ago_start <= room.create_time < three_days_ago_start:
                seven_days_ago_rooms.append(room)
            elif one_month_ago_start <= room.create_time < seven_days_ago_start:
                one_month_ago_rooms.append(room)

        # 序列化数据
        today_serializer = RoomSerializer(today_rooms, many=True)
        yesterday_serializer = RoomSerializer(yesterday_rooms, many=True)
        three_days_ago_serializer = RoomSerializer(three_days_ago_rooms, many=True)
        seven_days_ago_serializer = RoomSerializer(seven_days_ago_rooms, many=True)
        one_month_ago_serializer = RoomSerializer(one_month_ago_rooms, many=True)
        active_room_serializer = RoomSerializer(instance=active_room,many=True)

        return Response({
            '今天': today_serializer.data,
            '昨天': yesterday_serializer.data,
            '三天前': three_days_ago_serializer.data,
            '七天前': seven_days_ago_serializer.data,
            '一个月前': one_month_ago_serializer.data,
            'active_room': active_room_serializer.data
        })

    @action(detail=False, methods=['patch'])
    @transaction.atomic
    def update_active(self, request, *args, **kwargs):
        if not isinstance(request.data, list):
            return Response({'error': 'Expected a list of items.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # 从序列化器中提取已验证的数据
        instances = []
        for item in request.data:
            instance = Room.objects.get(id=item['id'])
            instance.active = item['active']
            instances.append(instance)

        # 使用 bulk_update 方法批量更新
        Room.objects.bulk_update(instances, ['active'])

        return Response(serializer.data, status=status.HTTP_200_OK)


class MessageView(ModelViewSet):
    queryset = Message.objects.all()
    pagination_class = None
    serializer_class = MessageSerializer
    filterset_fields = ['user', 'room']  # 过滤字段
