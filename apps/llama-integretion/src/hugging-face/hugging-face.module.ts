import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { HuggingFaceService } from './hugging-face.service';
import { HuggingFaceController } from './hugging-face.controller';

@Module({
  imports: [ConfigModule.forRoot({ isGlobal: true })],
  controllers: [HuggingFaceController],
  providers: [HuggingFaceService],
  exports: [HuggingFaceService],
})
export class HuggingFaceModule {}
