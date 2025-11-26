import { Injectable, Logger, BadRequestException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { GoogleGenAI } from '@google/genai';
import { PromptDto } from '@synthora/dto';

@Injectable()
export class GeminiService {
  private readonly googleAI: GoogleGenAI | null;
  private readonly model: string | null;

  constructor(private readonly configService: ConfigService) {
    const geminiApiKey = this.configService.get<string>('GEMINI_API_KEY');

    if (!geminiApiKey) {
      this.googleAI = null;
      this.model = null;
      return;
    }

    try {
      this.googleAI = new GoogleGenAI({ apiKey: geminiApiKey });
      this.model =
        this.configService.get<string>('GOOGLE_AI_MODEL') || 'gemini-2.5-flash';
    } catch (err) {
      Logger.error(
        `Failed to initialize Gemini SDK: ${err?.message || String(err)}`,
        err?.stack,
        'GeminiService',
      );
      this.googleAI = null;
      this.model = null;
    }
  }

  async make(payload: Partial<PromptDto>): Promise<any> {
    // Validate payload has required fields
    const hasContent =
      payload &&
      (payload.response !== undefined ||
        payload.responses !== undefined ||
        payload.input !== undefined ||
        payload.context !== payload.context ||
        payload.messages !== undefined ||
        payload.prompt !== undefined);

    if (!hasContent) {
      throw new BadRequestException(
        'Request body must include one of: response, responses, input, messages, or prompt',
      );
    }

    // Return predefined responses if provided
    if (payload.responses !== undefined) return payload.responses;
    if (payload.response !== undefined) return payload.response;

    if (!this.googleAI || !this.model) {
      throw new Error(
        'Gemini SDK not initialized. Check that GEMINI_API_KEY is set.',
      );
    }

    // Extract text input from payload
    let textInput = '';
    if (payload.input) {
      textInput = payload.input;
    } else if (payload.prompt) {
      textInput =
        typeof payload.prompt === 'string'
          ? payload.prompt
          : JSON.stringify(payload.prompt);
    } else if (payload.messages && Array.isArray(payload.messages)) {
      const lastMessage = payload.messages[payload.messages.length - 1];
      textInput = lastMessage?.content || lastMessage?.text || '';
    }

    // Call Gemini API
    const result = await this.googleAI.models.generateContent({
      model: this.model,
      contents: textInput,
      config: {
        systemInstruction: {
          role: 'system',
          text: payload.context || 'You are a helpful assistant.',
        },
      },
    });

    console.log('Gemini API response:', result);

    return {
      success: true,
      response: result.text,
      candidates: result.candidates,
      usageMetadata: result.usageMetadata,
    };
  }
}
