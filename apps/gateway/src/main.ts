import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { LoggingInterceptor } from './common/interceptors/logging.interceptor';
import { HttpExceptionFilter } from './common/filters/http-exception.filter';
import { ServicesConfig } from './config/services.config';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    bodyParser: true, // Explicitly enable body parser
  });

  app.useGlobalInterceptors(new LoggingInterceptor());
  app.useGlobalFilters(new HttpExceptionFilter());

  await app.listen(ServicesConfig.port);
  console.log(`🚀 Gateway running on port ${ServicesConfig.port}`);
}
bootstrap();
