import {
  CallHandler,
  ExecutionContext,
  Injectable,
  Logger,
  NestInterceptor,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import axios from 'axios';
import { ServicesConfig } from '../../config/services.config';

const log = new Logger('SaveChatInterceptor');

function normalizeAiValue(aiValue: any): {
  success: boolean;
  response: string;
} {
  try {
    if (!aiValue) return { success: false, response: '' };
    if (aiValue.error) {
      const err = aiValue.error;
      return { success: false, response: err.message || JSON.stringify(err) };
    }
    const data = aiValue.data ?? aiValue;
    if (!data) return { success: false, response: '' };
    if (typeof data === 'string') return { success: true, response: data };
    // common shapes
    if (data.response && typeof data.response === 'string')
      return { success: true, response: data.response };
    if (data.message && data.message.content)
      return { success: true, response: data.message.content };
    // fallback to JSON
    return { success: true, response: JSON.stringify(data) };
  } catch (e) {
    return { success: false, response: String(e) };
  }
}

@Injectable()
export class SaveChatInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const req = context.switchToHttp().getRequest();
    const headers = req.headers || {};
    const authHeader = headers['authorization'] || headers['Authorization'];

    // Attempt to resolve user via auth service if Authorization header is present
    let resolvedUserId: string | null = null;

    const tryResolveUser = async () => {
      if (!ServicesConfig.auth) return null;
      if (!authHeader) return null;
      try {
        const resp = await axios.get(`${ServicesConfig.auth}/auth/me`, {
          headers: { Authorization: authHeader },
          timeout: 5000,
        });
        const user = resp.data;
        // user may be object (user document) or wrapped; try common fields
        if (!user) return null;
        return user._id ?? user.id ?? user.userId ?? null;
      } catch (err) {
        log.debug('Could not resolve user from auth service: ' + err.message);
        return null;
      }
    };

    // Start resolving but don't block the request processing
    const resolvePromise = tryResolveUser().then((id) => {
      resolvedUserId = id;
    });

    return next.handle().pipe(
      tap((result) => {
        // Ensure user resolution finished (wait a bit) but don't block too long
        resolvePromise
          .catch(() => null)
          .finally(async () => {
            try {
              const userId = resolvedUserId;
              if (!userId) return;

              // Normalize gateway AI result into compact storage shape
              const aiPayload = result || {};
              const summary = aiPayload.summary ?? aiPayload;
              const rawResponses = aiPayload.rawResponses ?? {};

              const normalized = Object.fromEntries(
                Object.entries(rawResponses).map(([k, v]) => [
                  k,
                  normalizeAiValue(v),
                ]),
              );

              const dbPayload = {
                summary:
                  typeof summary === 'string' ? { result: summary } : summary,
                rawResponses: normalized,
              };

              // Fire-and-forget post to auth service to store the chat
              if (!ServicesConfig.auth) {
                log.debug('Auth service url not configured, skipping save');
                return;
              }

              await axios.post(
                `${ServicesConfig.auth}/users/${userId}/chats`,
                dbPayload,
                {
                  headers: {
                    Authorization: authHeader,
                    'Content-Type': 'application/json',
                  },
                  timeout: 5000,
                },
              );
              log.log(`Saved chat for user ${userId} to auth service`);
            } catch (e) {
              log.error('Failed to save chat to auth service: ' + e.message);
            }
          });
      }),
    );
  }
}
