import { Injectable, Logger, BadRequestException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { CohereClient } from 'cohere-ai';

@Injectable()
export class CohereService {
  private readonly cohereClient: CohereClient | null;
  private readonly model: string;

  constructor(private readonly configService: ConfigService) {
    const cohereApiKey = this.configService.get<string>('COHERE_API_KEY');

    if (!cohereApiKey) {
      this.cohereClient = null;
      this.model = 'command-r-plus-08-2024';
      return;
    }

    try {
      this.cohereClient = new CohereClient({
        token: cohereApiKey,
      });
      this.model =
        this.configService.get<string>('COHERE_MODEL') ||
        'command-r-plus-08-2024';
    } catch (err) {
      Logger.error(
        `Failed to initialize Cohere SDK: ${err?.message || String(err)}`,
        err?.stack,
        'CohereService',
      );
      this.cohereClient = null;
      this.model = 'command-r-plus-08-2024';
    }
  }

  async make(payload: any): Promise<any> {
    // Validate payload has required fields
    const hasContent =
      payload &&
      (payload.response !== undefined ||
        payload.responses !== undefined ||
        payload.input !== undefined ||
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

    if (!this.cohereClient) {
      throw new Error(
        'Cohere SDK not initialized. Check that COHERE_API_KEY is set.',
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

    // Call Cohere API
    try {
      const response = await this.cohereClient.chat({
        model: this.model,
        message: textInput,
      });

      return {
        success: true,
        response: response.text,
        generationId: response.generationId,
        finishReason: response.finishReason,
        meta: response.meta,
      };
    } catch (error) {
      Logger.error(
        `Cohere API error: ${error?.message || String(error)}`,
        error?.stack,
        'CohereService',
      );
      throw new BadRequestException(
        `Failed to generate response: ${error?.message || String(error)}`,
      );
    }
  }
}
