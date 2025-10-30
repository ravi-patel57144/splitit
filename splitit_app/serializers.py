from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Occasion, Event, Expenditure, ExpenditureSplit, Payment
from decimal import Decimal

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email']
        extra_kwargs = {
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }

    def validate_email(self, value: str) -> str:
        if not value:
            raise serializers.ValidationError('Email is required')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save()
        return user

class OccasionSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Occasion
        fields = ['id', 'name', 'description', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

class EventSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    occasion_name = serializers.CharField(source='occasion.name', read_only=True)
    
    class Meta:
        model = Event
        fields = ['id', 'name', 'description', 'occasion', 'occasion_name', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

class ExpenditureSplitSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ExpenditureSplit
        fields = ['id', 'user', 'user_id', 'amount', 'is_paid', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ExpenditureSerializer(serializers.ModelSerializer):
    paid_by = UserSerializer(read_only=True)
    splits = ExpenditureSplitSerializer(many=True, read_only=True)
    split_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of user IDs to split the expense among"
    )
    custom_amounts = serializers.ListField(
        child=serializers.DecimalField(max_digits=10, decimal_places=2),
        write_only=True,
        required=False,
        help_text="Custom amounts for each user (only for custom split)"
    )
    
    class Meta:
        model = Expenditure
        fields = [
            'id', 'event', 'amount', 'description', 'paid_by', 'split_type',
            'splits', 'split_user_ids', 'custom_amounts', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'paid_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('split_type') == 'custom':
            custom_amounts = data.get('custom_amounts', [])
            split_user_ids = data.get('split_user_ids', [])
            
            if not custom_amounts or not split_user_ids:
                raise serializers.ValidationError("Custom amounts and user IDs are required for custom split")
            
            if len(custom_amounts) != len(split_user_ids):
                raise serializers.ValidationError("Number of custom amounts must match number of users")
            
            if sum(custom_amounts) != data['amount']:
                raise serializers.ValidationError("Sum of custom amounts must equal the total amount")
        
        return data
    
    def create(self, validated_data):
        split_user_ids = validated_data.pop('split_user_ids', [])
        custom_amounts = validated_data.pop('custom_amounts', [])
        split_type = validated_data.get('split_type', 'equal')
        
        expenditure = Expenditure.objects.create(**validated_data)
        
        if split_type == 'equal':
            # Equal split among all users
            if split_user_ids:
                amount_per_user = expenditure.amount / len(split_user_ids)
                for user_id in split_user_ids:
                    ExpenditureSplit.objects.create(
                        expenditure=expenditure,
                        user_id=user_id,
                        amount=amount_per_user
                    )
        else:
            # Custom split
            for user_id, amount in zip(split_user_ids, custom_amounts):
                ExpenditureSplit.objects.create(
                    expenditure=expenditure,
                    user_id=user_id,
                    amount=amount
                )
        
        return expenditure

class PaymentSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    to_user_id = serializers.IntegerField(write_only=True)
    expenditure_split_id = serializers.IntegerField(source='expenditure_split.id', read_only=True)
    expenditure_split = serializers.PrimaryKeyRelatedField(
        queryset=ExpenditureSplit.objects.all(), write_only=True, required=False, allow_null=True
    )
    
    class Meta:
        model = Payment
        fields = [
            'id', 'from_user', 'to_user', 'to_user_id', 'amount', 'description',
            'status', 'created_at', 'updated_at', 'expenditure_split_id', 'expenditure_split'
        ]
        read_only_fields = ['id', 'from_user', 'created_at', 'updated_at']

class UserBalanceSerializer(serializers.Serializer):
    user = UserSerializer()
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    total_owed = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    total_owes = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)

class OccasionSummarySerializer(serializers.Serializer):
    occasion = OccasionSerializer()
    total_expenditures = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    total_events = serializers.IntegerField()
    user_balances = UserBalanceSerializer(many=True)
