import { Controller, Post, Body } from '@nestjs/common';
import { GeminiService } from './gemini.service';
import { PromptDto } from '@synthora/dto';

@Controller('gemini')
export class GeminiController {
  constructor(private readonly geminiService: GeminiService) {}

  @Post('make')
  async make(@Body() body: PromptDto) {
    return await this.geminiService.make(body);
  }
}
