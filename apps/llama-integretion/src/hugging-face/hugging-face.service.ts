import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PromptDto } from '@synthora/dto';
import { OpenAI } from 'openai';

@Injectable()
export class HuggingFaceService {
  private client: OpenAI;

  constructor(private configService: ConfigService) {
    this.client = new OpenAI({
      baseURL: 'https://router.huggingface.co/v1',
      apiKey: this.configService.get<string>('HF_TOKEN'),
    });
  }

  async generateCompletion(message: PromptDto) {
    try {
      const chatCompletion = await this.client.chat.completions.create({
        model: this.configService.get<string>('HF_MODEL') as string,
        messages: [
          {
            content: message.input ?? message.prompt,
            role: 'user',
          },
        ],
      });

      return {
        success: true,
        message: chatCompletion.choices[0].message,
        usage: chatCompletion.usage,
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
      };
    }
  }
}
