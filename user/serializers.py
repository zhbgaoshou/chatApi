from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['image']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    image = serializers.ImageField(write_only=True, required=False)
    date_joined = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "date_joined", 'profile', 'image']
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 6},
        }

    def create(self, validated_data):
        # 从验证后的数据中提取出 image
        image = validated_data.pop('image', None)

        # 创建用户
        user = User.objects.create_user(**validated_data)

        # 创建或获取已存在的 Profile 并关联图片
        Profile.objects.create(user=user, image=image)

        return user

    def update(self, instance, validated_data):
        # 提取 image
        image = validated_data.pop('image', None)

        # 更新用户的其他信息
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)

        if 'password' in validated_data:
            instance.set_password(validated_data['password'])

        instance.save()

        # 更新或创建 Profile
        profile, created = Profile.objects.get_or_create(user=instance)
        if image:
            profile.image = image
        profile.save()

        return instance
