import datetime
from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import relationship, Mapped, mapped_column
from models.databases import Base
from typing import List
from .enums import *


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(nullable=True)
    admin: Mapped[bool] = mapped_column(default=False)
    chat_model: Mapped[ChatModelEnum] = mapped_column(nullable=True, default=ChatModelEnum.GPT_4O_MINI)
    image_model: Mapped[ImageModelEnum] = mapped_column(nullable=True, default=ImageModelEnum.DALL_E_3)
    rate_id: Mapped[int] = mapped_column(ForeignKey('rate.id', ondelete="CASCADE"), index=True)
    last_activity_time: Mapped[datetime.datetime] = mapped_column(nullable=True, default=datetime.datetime.now)
    registration_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now, nullable=True)
    subscription_end_time: Mapped[datetime.datetime] = mapped_column(nullable=True)
    remaining_midjourney_generations: Mapped[int] = mapped_column(default=0, nullable=True)

    rate: Mapped['Rate'] = relationship('Rate', back_populates='users', lazy="joined")
    count_of_requests: Mapped[List['CountOfRequests']] = relationship('CountOfRequests', back_populates='user')
    messages: Mapped[List['AIMessage']] = relationship('AIMessage', back_populates='user')
    midjourney_prompts: Mapped[List['MidJourneyPrompts']] = relationship('MidJourneyPrompts', back_populates='user')
    
    @property
    def count_of_requests_dict(self):
        return {cor.model.name: cor.count for cor in self.count_of_requests}

class Rate(Base):
    __tablename__ = 'rate'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=True)
    models_limits: Mapped[List["ModelLimit"]] = relationship('ModelLimit', back_populates='rate', lazy="joined")
    price: Mapped[int] = mapped_column(nullable=True)
    users: Mapped[List["User"]] = relationship('User', back_populates='rate')
    midjourney_generations: Mapped[int] = mapped_column(nullable=True)
    price_3: Mapped[int] = mapped_column(nullable=True)
    price_6: Mapped[int] = mapped_column(nullable=True)
    price_12: Mapped[int] = mapped_column(nullable=True)
    
    @property
    def daily_limit_dict(self):
        return {
            model_limit.model: model_limit.daily_limit
            for model_limit in self.models_limits
        }
    
class ModelLimit(Base):
    __tablename__ = 'model_limits'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    rate_id: Mapped[int] = mapped_column(ForeignKey('rate.id', ondelete="CASCADE"), index=True)
    rate: Mapped[Rate] = relationship('Rate', back_populates='models_limits')
    model: Mapped[str] = mapped_column(nullable=True)
    daily_limit: Mapped[int] = mapped_column(nullable=True)

class CountOfRequests(Base):
    __tablename__ = 'counts_of_requests'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="CASCADE"), index=True)
    user: Mapped[User] = relationship('User', back_populates='count_of_requests')
    model: Mapped[ModelsEnum] = mapped_column(nullable=True)
    count: Mapped[int] = mapped_column(default=0)
    
class AIMessage(Base):
    __tablename__ = 'messages'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="CASCADE"), index=True)
    user: Mapped[User] = relationship('User', back_populates='messages')
    content: Mapped[str] = mapped_column(nullable=True)
    role: Mapped[str] = mapped_column(nullable=True)
    time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    
class MidJourneyPrompts(Base):
    __tablename__ = 'midjourney_prompts'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    prompt: Mapped[str] = mapped_column(nullable=True)
    type_: Mapped[str] = mapped_column(nullable=True)
    hash: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=True)
    progress: Mapped[int] = mapped_column(nullable=True)
    result: Mapped[str] = mapped_column(nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="CASCADE"), index=True)
    user: Mapped[User] = relationship('User', back_populates='midjourney_prompts')

class MidJourneyPrices(Base):
    __tablename__ = 'midjourney_prices'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    price: Mapped[int] = mapped_column(nullable=True)
    count_of_generations: Mapped[int] = mapped_column(nullable=True)