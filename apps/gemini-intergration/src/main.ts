import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { ValidationPipe, Logger } from '@nestjs/common';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  // Global validation pipe: transforms payloads to DTO instances and
  // rejects invalid requests with 400 responses.
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
    }),
  );

  if (!process.env.PORT) {
    throw new Error('PORT environment variable is not defined');
  }

  Logger.log(
    `Server starting on http://localhost:${process.env.PORT}`,
    'Bootstrap',
  );

  await app.listen(process.env.PORT);
}

bootstrap();
