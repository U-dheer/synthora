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

    // Explicitly allow signup/login/register endpoints without auth
    if (
      rawPath.startsWith('/auth/login') ||
      rawPath.startsWith('/auth/signup') ||
      rawPath.startsWith('/auth/register')
    ) {
      return true;
    }

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
        return true;
      }
    }

    const getTokenFromRequest = (req: any): string | null => {
      const header = req.headers?.authorization || req.headers?.Authorization;
      if (header && typeof header === 'string') {
        if (header.startsWith('Bearer ')) return header.slice(7);
        return header;
      }
      if (req.headers && req.headers['x-access-token'])
        return req.headers['x-access-token'];
      if (req.cookies && req.cookies.access_token)
        return req.cookies.access_token;
      const cookieHeader = req.headers?.cookie;
      if (cookieHeader && typeof cookieHeader === 'string') {
        const m = cookieHeader.match(/(?:^|;\s*)access_token=([^;]+)/);
        if (m) return decodeURIComponent(m[1]);
      }
      return null;
    };

    const token = getTokenFromRequest(req);
    if (!token) {
      throw new UnauthorizedException('Authorization token missing');
    }

    const serviceSharedSecret = (ServicesConfig as any).serviceSharedSecret;
    if (serviceSharedSecret) {
      const expectedHeader = `Bearer ${serviceSharedSecret}`;
      if (authHeader === expectedHeader || token === serviceSharedSecret) {
        req.userId = 'service';
        req.user = { service: true };
        return true;
      }
    }

    if (!ServicesConfig.auth) {
      log.error('Auth service URL not configured (ServicesConfig.auth)');
      throw new UnauthorizedException('Auth service not available');
    }

    try {
      const resp = await axios.get(`${ServicesConfig.auth}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 5000,
      });

      const user = resp.data;
      if (!user) {
        throw new UnauthorizedException('User not found');
      }

      req.user = user;
      req.userId = user._id ?? user.id ?? user.userId ?? null;
      return true;
    } catch (err: any) {
      log.debug('Auth validation failed: ' + (err?.message || err));
      throw new UnauthorizedException('Invalid or expired token');
    }
  }
}
