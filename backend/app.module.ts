import { Module, MiddlewareConsumer, NestModule } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { RedisModule } from '@nestjs-modules/ioredis';
import { AuthModule } from './modules/auth/auth.module';
import { LocaleMiddleware } from './modules/i18n/locale.middleware';
import { AuthMiddleware } from './modules/auth/auth.middleware';
import { LanguageDetector } from './modules/i18n/language.detector';
import { TranslationService } from './modules/i18n/translation.service';
import { AiService } from './modules/ai/ai.service';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    RedisModule.forRoot({
      type: 'single',
      url: 'process.env.REDIS_URL || 'redis://:wanderix_redis@localhost:6379'',
    }),
    AuthModule,
  ],
  providers: [
    LanguageDetector,
    TranslationService,
    AiService,
  ],
})
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {url: process.env.REDIS_URL || 'redis://:wanderix_redis@localhost:6379',
    consumer
      .apply(LocaleMiddleware, AuthMiddleware)
      .forRoutes('*');
  }
}
