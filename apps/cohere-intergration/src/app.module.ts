import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { CohereModule } from './cohere/cohere.module';
import { ConfigModule } from '@nestjs/config';

@Module({
  imports: [CohereModule, ConfigModule.forRoot({ isGlobal: true })],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
