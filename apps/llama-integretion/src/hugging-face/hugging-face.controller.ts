import { Body, Controller, Post, Headers } from '@nestjs/common';
import { HuggingFaceService } from './hugging-face.service';
import { PromptDto } from '@synthora/dto';

@Controller('hugging-face')
export class HuggingFaceController {
  constructor(private readonly huggingFaceService: HuggingFaceService) {}

  @Post('chat')
  async generateChat(
    @Body() body: PromptDto,
    @Headers('authorization') authorization?: string,
  ) {
    return this.huggingFaceService.generateCompletion(body, authorization);
  }
}
