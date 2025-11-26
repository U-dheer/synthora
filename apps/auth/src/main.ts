import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { ValidationPipe } from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import * as express from 'express';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
    }),
  );

  const config = new DocumentBuilder()
    .setTitle('Eclipso POS API')
    .setDescription(
      'A comprehensive RESTful API for the Eclipso Point-of-Sale system. This API provides secure endpoints for authentication, multi-tenant organization management, user administration, and core business operations. Built with NestJS and designed for retail and hospitality environments, it supports real-time synchronization, role-based access control, and seamless third-party integrations.',
    )
    .setVersion('1.0')
    .addBearerAuth(
      {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
        in: 'header',
      },
      'Authorization',
    )
    .addServer(process.env.API_URL || 'http://localhost:3000')
    .build();

  const document = SwaggerModule.createDocument(app, config, {
    deepScanRoutes: true,
  });
  document.security = [{ Authorization: [] }];

  // Expose the OpenAPI JSON at /api-json (useful for tools)
  app
    .getHttpAdapter()
    .get('/api-json', (req: express.Request, res: express.Response) => {
      res.json(document);
    });

  // Standard Swagger UI at /docs
  SwaggerModule.setup('docs', app, document);

  // Optional: dynamically load Scalar API Reference if available
  try {
    const { apiReference } = await import('@scalar/nestjs-api-reference');

    app.use(
      '/api-reference',
      apiReference({
        darkMode: true,
        theme: 'moon',
        title: 'Eclipso POS API Reference',
        content: document,
      }),
    );
  } catch (err) {
    // If Scalar isn't installed, continue silently. Install instructions provided below.
  }

  const port = process.env.PORT ?? 3000;
  await app.listen(port);
}

bootstrap();
