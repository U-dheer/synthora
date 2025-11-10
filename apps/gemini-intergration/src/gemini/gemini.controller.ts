import { Controller, Post, Body } from '@nestjs/common';
import { GeminiService } from './gemini.service';
import { CreateGeminiDto } from '@synthora/dto';

@Controller('gemini')
export class GeminiController {
  constructor(private readonly geminiService: GeminiService) {}

  @Post('make')
  async make(@Body() body: CreateGeminiDto) {
    return await this.geminiService.make(body);
  }
}
