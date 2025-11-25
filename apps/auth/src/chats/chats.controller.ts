import {
  Body,
  Controller,
  Get,
  Param,
  Post,
  Query,
  UseGuards,
  ForbiddenException,
} from '@nestjs/common';
import { ChatsService } from './chats.service';
import { CreateChatResponseDto } from './dtos/create-chat-response.dto';
import { AuthGuard } from 'src/guards/auth.guard';
import { RequestUser } from 'src/decorators/request-user.decorator';

@Controller('users/:userId/chats')
export class ChatsController {
  constructor(private readonly chatsService: ChatsService) {}

  @UseGuards(AuthGuard)
  @Post()
  async create(
    @RequestUser() authUserId: string,
    @Param('userId') userId: string,
    @Body() dto: CreateChatResponseDto,
  ) {
    if (!authUserId || String(authUserId) !== String(userId)) {
      throw new ForbiddenException('Cannot create chat for other user');
    }
    return this.chatsService.createForUser(userId, dto);
  }

  @UseGuards(AuthGuard)
  @Get()
  async list(
    @RequestUser() authUserId: string,
    @Param('userId') userId: string,
    @Query('limit') limit?: string,
    @Query('skip') skip?: string,
  ) {
    if (!authUserId || String(authUserId) !== String(userId)) {
      throw new ForbiddenException('Cannot list chats for other user');
    }
    return this.chatsService.findForUser(
      userId,
      limit ? Number(limit) : 50,
      skip ? Number(skip) : 0,
    );
  }
}
