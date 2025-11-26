import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model, Types } from 'mongoose';
import { ChatResponse, ChatResponseDocument } from './chat-response.schema';
import { CreateChatResponseDto } from './dtos/create-chat-response.dto';

@Injectable()
export class ChatsService {
  constructor(
    @InjectModel(ChatResponse.name)
    private chatModel: Model<ChatResponseDocument>,
  ) {}

  async createForUser(
    userId: string | Types.ObjectId,
    dto: CreateChatResponseDto,
  ) {
    const doc = await this.chatModel.create({
      userId: new Types.ObjectId(String(userId)),
      ...dto,
    });
    return doc;
  }

  async findForUser(userId: string | Types.ObjectId, limit = 50, skip = 0) {
    return this.chatModel
      .find({ userId: new Types.ObjectId(String(userId)) })
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limit)
      .lean();
  }
}
