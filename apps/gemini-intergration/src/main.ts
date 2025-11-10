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

  const port = Number(process.env.PORT) || 3000;
  Logger.log(`Server starting on http://localhost:${port}`, 'Bootstrap');

  await app.listen(port);
}

bootstrap();
