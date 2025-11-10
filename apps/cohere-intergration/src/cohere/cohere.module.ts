import { Module } from '@nestjs/common';
import { CohereController } from './cohere.controller';
import { CohereService } from './cohere.service';

@Module({
  controllers: [CohereController],
  providers: [CohereService],
})
export class CohereModule {}
