import { Injectable, HttpException, Logger } from '@nestjs/common';
import axios from 'axios';
import { resolveServiceUrl } from '../utils/url-resolver';
import { ServicesConfig } from '../config/services.config';
import { ContextWindowBuilder } from 'src/utils/context-window.util';

// In-memory backoff tracking for Gemini quota errors
let lastGemini429At = 0;
const GEMINI_BACKOFF_MS = 60 * 1000; // 60 seconds

@Injectable()
export class GatewayService {
  async handleAIRequest(question: string) {
    try {
      console.log('Handling AI request for question:', question);
      console.log('Calling AI models...');
      console.log('Gemini URL:', `${ServicesConfig.gemini}/gemini/make`);
      console.log('Cohere URL:', `${ServicesConfig.cohere}/cohere/make`);
      console.log('Llama URL:', `${ServicesConfig.llama}/hugging-face/chat`);

      const requestBody = { input: question };

      const geminiPromise = await axios.post(
        `${ServicesConfig.gemini}/gemini/make`,
        requestBody,
      );

      const coherePromise = await axios.post(
        `${ServicesConfig.cohere}/cohere/make`,
        requestBody,
      );

      const llamaPromise = await axios.post(
        `${ServicesConfig.llama}/hugging-face/chat`,
        requestBody,
      );

      const settled = await Promise.allSettled([
        geminiPromise,
        coherePromise,
        llamaPromise,
      ]);

      const geminiRes =
        settled[0].status === 'fulfilled'
          ? settled[0].value
          : { error: settled[0].reason };
      const cohereRes =
        settled[1].status === 'fulfilled'
          ? settled[1].value
          : { error: settled[1].reason };
      const llamaRes =
        settled[2].status === 'fulfilled'
          ? settled[2].value
          : { error: settled[2].reason };

      const geminiAny: any = geminiRes;
      const cohereAny: any = cohereRes;
      const llamaAny: any = llamaRes;

      try {
        const geminiErrorStatus =
          geminiAny?.error?.response?.status || geminiAny?.error?.status;
        if (geminiErrorStatus === 429) {
          lastGemini429At = Date.now();
          console.log(
            'Gemini returned 429 -> enabling backoff for',
            GEMINI_BACKOFF_MS,
            'ms',
          );
        }
        if (geminiAny?.skipped) {
          console.log('Gemini call skipped due to backoff');
        }
      } catch (e) {}

      console.log('AI model call results:', {
        gemini: geminiAny.error
          ? `ERROR: ${geminiAny.error.message || geminiAny.error}`
          : 'OK',
        cohere: cohereAny.error
          ? `ERROR: ${cohereAny.error.message || cohereAny.error}`
          : 'OK',
        llama: llamaAny.error
          ? `ERROR: ${llamaAny.error.message || llamaAny.error}`
          : 'OK',
      });

      const responses = {
        ai1: geminiAny.error ? geminiAny.error : geminiAny.data,
        ai2: cohereAny.error ? cohereAny.error : cohereAny.data,
        ai3: llamaAny.error ? llamaAny.error : llamaAny.data,
      };

      console.log('AI model responses received');
      console.log('Sending to summarizer...');

      // Try to summarize, but if it fails, use the first AI response (Gemini)
      let summary;
      try {
        const summarizerBase = (ServicesConfig.summarizer || '')
          .replace(/\/summarize\/?$/i, '')
          .replace(/\/$/, '');

        console.log('Summarizer base URL:', summarizerBase);

        const summaryRes = await axios.post(
          `${summarizerBase}/api/summarize/ai-prompts`,
          {
            ai1:
              typeof geminiAny.data === 'string'
                ? geminiAny.data
                : JSON.stringify(geminiAny.data),
            ai2:
              typeof cohereAny.data === 'string'
                ? cohereAny.data
                : JSON.stringify(cohereAny.data),
            ai3:
              typeof llamaAny.data === 'string'
                ? llamaAny.data
                : JSON.stringify(llamaAny.data),
          },
        );

        console.log('Summarizer responded successfully!');
        summary = summaryRes.data;
      } catch (summarizerError) {
        console.log(
          ' Summarizer unavailable, using first available AI response',
        );
        let fallbackData: any = null;
        if (!cohereAny.error) fallbackData = cohereAny.data;
        else if (!llamaAny.error) fallbackData = llamaAny.data;
        else if (!geminiAny.error) fallbackData = geminiAny.data;
        else
          fallbackData = geminiAny.error || cohereAny.error || llamaAny.error;

        if (fallbackData?.response) {
          summary = fallbackData.response;
        } else if (fallbackData?.message?.content) {
          summary = fallbackData.message.content;
        } else if (typeof fallbackData === 'string') {
          summary = fallbackData;
        } else {
          summary = JSON.stringify(fallbackData);
        }
      }

      return {
        summary: summary,
        rawResponses: responses,
      };
    } catch (error) {
      console.error('Error in handleAIRequest:', error.message);
      console.error('Error details:', error.response?.data);
      console.error('Error status:', error.response?.status);
      throw new HttpException(
        error.response?.data?.message || error.message,
        error.response?.status || 500,
      );
    }
  }

  async forwardRequest(
    method: string,
    path: string,
    body?: any,
    headers?: any,
  ) {
    try {
      const serviceUrl = resolveServiceUrl(path);
      console.log('Resolved service URL:', serviceUrl);

      let forwardedPath = path;
      if (path.startsWith('/gemini')) {
        forwardedPath = path.replace(/^\/gemini/, '');
      } else if (path.startsWith('/cohere')) {
        forwardedPath = path.replace(/^\/cohere/, '');
      } else if (path.startsWith('/llama')) {
        forwardedPath = path.replace(/^\/llama/, '');
      }

      const candidatePaths: string[] = [forwardedPath];
      if (path.startsWith('/auth')) {
        const stripped = path.replace(/^\/auth/, '') || '/';
        if (stripped !== forwardedPath) candidatePaths.push(stripped);
      }

      const serviceUrlNormalized = serviceUrl.endsWith('/')
        ? serviceUrl.slice(0, -1)
        : serviceUrl;

      for (const cand of candidatePaths) {
        const targetUrl = `${serviceUrlNormalized}${cand}`;
        console.log('Forwarding request to:', targetUrl);
        console.log('Request method:', method);
        console.log('Request body:', body);
        try {
          console.log('Making axios request...');
          const forwardedHeaders: any = {
            Accept: headers?.['accept'] || '*/*',
            ...(headers?.['authorization'] && {
              Authorization: headers['authorization'],
            }),
            ...(headers?.['cookie'] && { Cookie: headers['cookie'] }),
          };

          if (headers?.['content-type']) {
            forwardedHeaders['Content-Type'] = headers['content-type'];
          }

          const response = await axios.request({
            method,
            url: targetUrl,
            data: body,
            headers: forwardedHeaders,
            timeout: 30000,
            maxBodyLength: Infinity,
            maxContentLength: Infinity,
          });

          console.log('Response received from target service:', response.data);

          const question = body?.question || body?.query;

          if (!question) {
            return response.data;
          }

          try {
            const aiResponse = await this.handleAIRequest(question);

            return {
              answer: aiResponse.summary,
              query_type: 'ai_generated',
              retrieved_contexts: [],
              llm_responses: [
                { service: 'gemini', response: aiResponse.rawResponses.ai1 },
                { service: 'cohere', response: aiResponse.rawResponses.ai2 },
                { service: 'llama', response: aiResponse.rawResponses.ai3 },
              ],
              processing_time_seconds: 0,
              timestamp: new Date().toISOString(),
            };
          } catch (aiError) {
            console.error('AI orchestration failed:', aiError.message);
            return response.data;
          }
        } catch (error) {
          console.error(`Error forwarding`, error.message);
          continue;
        }
      }
    } catch (error) {
      console.error('Error in forwardRequest:', error.message);
      console.error('Error details:', error.response?.data);
      console.error('Error status:', error.response?.status);
      console.error('Full error:', error);
      throw new HttpException(
        error.response?.data?.message || error.message,
        error.response?.status || 500,
      );
    }
  }

  async handleAIStreamRequest(question: string, files?: any[]) {
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();

        const sendEvent = (event: string, data: any) => {
          const message = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
          controller.enqueue(encoder.encode(message));
        };

        // Accumulate all responses
        const responses: any = {
          gemini_res: null,
          cohere_res: null,
          llama_res: null,
          summary: null,
        };

        try {
          console.log('Starting streaming AI request for question:', question);

          const context = new ContextWindowBuilder()
            .setSystemPrompt(
              `
You are a helpful and reliable AI assistant.

You MUST use the information provided in the "UPLOADED FILE CONTENT" section as your primary reference when answering the user's question. Treat these RAG chunks as authoritative context.

Rules:
1. If the uploaded content contains information relevant to the user's question, use it to generate a clear and accurate answer.
2. If the uploaded content does NOT contain information relevant to the user's question, respond by saying:
   "I can help you with that, but the uploaded content does not contain information related to your question."
3. Do NOT hallucinate or invent facts not supported by the uploaded content.
4. If additional information is needed to answer properly, state what is missing.
5. Always keep responses grounded, clear, and directly focused on the user's question.

Your output should always rely strictly on the context unless it is missing.

          `,
            )
            .addRagChunks([
              'Sri Lanka,[a] officially the Democratic Socialist Republic of Sri Lanka, formerly known as Ceylon,[b] is an island country in South Asia. It is located in the Indian Ocean, southwest of the Bay of Bengal, and is separated from India by',
              'is separated from India by the Gulf of Mannar and the Palk Strait. It shares a maritime border with the Maldives in the southwest and India in the northwest, and it lies across the Bay of Bengal from Bangladesh and',
              'of Bengal from Bangladesh and Myanmar in the northeast and the Andaman and Nicobar Islands in the east. Sri Jayawardenepura Kotte is the legislative capital of Sri Lanka, while the largest city, Colombo, is the administrative and judicial capital which',
              "administrative and judicial capital which is the nation's political, financial and cultural centre. Kandy is the second-largest city and also the capital of the last native kingdom of Sri Lanka. The majority of the population speak Sinhala, while Tamil is",
              'speak Sinhala, while Tamil is the second most-spoken language. They are spoken by approximately 17 million and 5 million people respectively.',
            ] as string[])
            .build();

          console.log('context', context);

          const requestBody = { input: question, context: context };

          // Call Gemini
          sendEvent('status', { model: 'gemini', status: 'requesting gemini' });
          try {
            const geminiRes = await axios.post(
              `${ServicesConfig.gemini}/gemini/make`,
              requestBody,
            );
            responses.gemini_res = geminiRes.data;
            sendEvent('status', { model: 'gemini', status: 'completed' });
          } catch (geminiError: any) {
            const geminiErrorStatus =
              geminiError?.response?.status || geminiError?.status;
            if (geminiErrorStatus === 429) {
              lastGemini429At = Date.now();
              console.log('Gemini returned 429 -> enabling backoff');
            }
            responses.gemini_res = {
              error: geminiError.message || 'Request failed',
            };
            sendEvent('status', { model: 'gemini', status: 'failed' });
          }

          // Call Cohere
          sendEvent('status', { model: 'cohere', status: 'requesting cohere' });
          try {
            const cohereRes = await axios.post(
              `${ServicesConfig.cohere}/cohere/make`,
              requestBody,
            );
            responses.cohere_res = cohereRes.data;
            sendEvent('status', { model: 'cohere', status: 'completed' });
          } catch (cohereError: any) {
            responses.cohere_res = {
              error: cohereError.message || 'Request failed',
            };
            sendEvent('status', { model: 'cohere', status: 'failed' });
          }

          // Call Llama
          sendEvent('status', { model: 'llama', status: 'requesting llama' });
          try {
            const llamaRes = await axios.post(
              `${ServicesConfig.llama}/hugging-face/chat`,
              requestBody,
            );
            responses.llama_res = llamaRes.data;
            sendEvent('status', { model: 'llama', status: 'completed' });
          } catch (llamaError: any) {
            responses.llama_res = {
              error: llamaError.message || 'Request failed',
            };
            sendEvent('status', { model: 'llama', status: 'failed' });
          }

          // Call Summarizer
          sendEvent('status', {
            model: 'summarizer',
            status: 'requesting summarizer',
          });
          try {
            const summarizerBase = (ServicesConfig.summarizer || '')
              .replace(/\/summarize\/?$/i, '')
              .replace(/\/$/, '');

            const summaryRes = await axios.post(
              `${summarizerBase}/api/summarize/ai-prompts`,
              {
                ai1:
                  typeof responses.gemini_res === 'string'
                    ? responses.gemini_res
                    : JSON.stringify(responses.gemini_res),
                ai2:
                  typeof responses.cohere_res === 'string'
                    ? responses.cohere_res
                    : JSON.stringify(responses.cohere_res),
                ai3:
                  typeof responses.llama_res === 'string'
                    ? responses.llama_res
                    : JSON.stringify(responses.llama_res),
              },
            );

            responses.summary = summaryRes.data;
            sendEvent('status', { model: 'summarizer', status: 'completed' });
          } catch (summarizerError: any) {
            console.log(
              'Summarizer unavailable, using first available AI response',
            );
            // Fallback logic
            let fallbackData: any = null;
            if (!responses.cohere_res?.error)
              fallbackData = responses.cohere_res;
            else if (!responses.llama_res?.error)
              fallbackData = responses.llama_res;
            else if (!responses.gemini_res?.error)
              fallbackData = responses.gemini_res;
            else
              fallbackData =
                responses.gemini_res ||
                responses.cohere_res ||
                responses.llama_res;

            if (fallbackData?.response) {
              responses.summary = fallbackData.response;
            } else if (fallbackData?.message?.content) {
              responses.summary = fallbackData.message.content;
            } else if (typeof fallbackData === 'string') {
              responses.summary = fallbackData;
            } else {
              responses.summary = JSON.stringify(fallbackData);
            }
            sendEvent('status', { model: 'summarizer', status: 'failed' });
          }

          // Send complete data with all responses
          sendEvent('complete', {
            message: 'All AI models processed',
            data: responses,
          });
          controller.close();
        } catch (error: any) {
          console.error('Error in handleAIStreamRequest:', error.message);
          sendEvent('error', {
            model: 'system',
            error: error.message || 'Stream failed',
            data: responses,
          });
          controller.close();
        }
      },
    });

    return stream;
  }
}
