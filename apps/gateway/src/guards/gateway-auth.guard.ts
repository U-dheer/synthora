import {
  CanActivate,
  ExecutionContext,
  Injectable,
  Logger,
  UnauthorizedException,
} from '@nestjs/common';
import axios from 'axios';
import { ServicesConfig } from '../config/services.config';

const log = new Logger('GatewayAuthGuard');

@Injectable()
export class GatewayAuthGuard implements CanActivate {
  async canActivate(context: ExecutionContext): Promise<boolean> {
    const req = context.switchToHttp().getRequest();
    const authHeader = req.headers?.authorization || req.headers?.Authorization;

    // Check public/whitelisted paths first. Support optional METHOD:pattern entries
    // in ServicesConfig.publicPaths like `GET:/public/*` or `/auth/login`.
    const rawPath = req.url || req.originalUrl || req.path || '';
    const method = (req.method || 'GET').toUpperCase();

    const publicPaths: string[] = ServicesConfig.publicPaths || [];

    const pathMatches = (pattern: string, path: string): boolean => {
      if (!pattern) return false;
      // simple prefix wildcard: '/public/*' -> startsWith('/public/')
      if (pattern.endsWith('*')) {
        const prefix = pattern.slice(0, -1);
        return path.startsWith(prefix);
      }
      return path === pattern;
    };

    for (const entry of publicPaths) {
      // allow entries like 'GET:/public/*' or just '/auth/login'
      const trimmed = (entry || '').trim();
      if (!trimmed) continue;
      let entryMethod: string | null = null;
      let pattern = trimmed;
      const colonIdx = trimmed.indexOf(':');
      if (colonIdx > 0) {
        entryMethod = trimmed.slice(0, colonIdx).toUpperCase();
        pattern = trimmed.slice(colonIdx + 1);
      }

      if (entryMethod && entryMethod !== method) continue;
      if (pathMatches(pattern, rawPath)) {
        // Public path - allow without auth
        return true;
      }
    }

    // Not public - require Authorization header
    if (!authHeader) {
      throw new UnauthorizedException('Authorization header missing');
    }
    // Shortcut: allow a pre-shared service token to authenticate internal
    // service-to-gateway calls. This is useful for trusted internal services
    // (like the RAG service) that cannot easily perform full user auth.
    const serviceSharedSecret = (ServicesConfig as any).serviceSharedSecret;
    if (serviceSharedSecret) {
      const expected = `Bearer ${serviceSharedSecret}`;
      if (authHeader === expected) {
        // Mark request as coming from a trusted service
        req.userId = 'service';
        return true;
      }
    }

    // Forward the exact Authorization header to the auth service's /auth/me
    if (!ServicesConfig.auth) {
      log.error('Auth service URL not configured (ServicesConfig.auth)');
      throw new UnauthorizedException('Auth service not available');
    }

    try {
      const resp = await axios.get(`${ServicesConfig.auth}/auth/me`, {
        headers: { Authorization: authHeader },
        timeout: 5000,
      });

      const user = resp.data;
      if (!user) {
        throw new UnauthorizedException('User not found');
      }

      // Attach resolved user id to request for downstream handlers/interceptors
      req.userId = user._id ?? user.id ?? user.userId ?? null;
      return true;
    } catch (err: any) {
      log.debug('Auth validation failed: ' + (err?.message || err));
      throw new UnauthorizedException('Invalid or expired token');
    }
  }
}
