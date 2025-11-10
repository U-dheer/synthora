import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { HuggingFaceModule } from './hugging-face/hugging-face.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    HuggingFaceModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
