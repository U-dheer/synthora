import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { ChatsController } from './chats.controller';
import { ChatsService } from './chats.service';
import { ChatResponse, ChatResponseSchema } from './chat-response.schema';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: ChatResponse.name, schema: ChatResponseSchema },
    ]),
  ],
  controllers: [ChatsController],
  providers: [ChatsService],
  exports: [ChatsService],
})
export class ChatsModule {}
