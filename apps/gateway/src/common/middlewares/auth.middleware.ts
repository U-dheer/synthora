import {
  Injectable,
  NestMiddleware,
  UnauthorizedException,
} from '@nestjs/common';

@Injectable()
export class AuthMiddleware implements NestMiddleware {
  use(req: any, _res: any, next: () => void) {
    const authHeader = req.headers['authorization'];
    if (!authHeader)
      throw new UnauthorizedException('No Authorization header found');
    next();
  }
}
