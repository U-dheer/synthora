import { Controller, Post, Body } from '@nestjs/common';
import { CohereService } from './cohere.service';
import { PromptDto } from '@synthora/dto';

@Controller('cohere')
export class CohereController {
  constructor(private readonly cohereService: CohereService) {}

  @Post('make')
  async make(@Body() body: PromptDto): Promise<any> {
    return await this.cohereService.make(body);
  }
}
