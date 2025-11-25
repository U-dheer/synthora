import {
  BadRequestException,
  Injectable,
  Logger,
  UnauthorizedException,
} from '@nestjs/common';
import { signUpDataDto } from './dtos/signUpData.Dto';
import { InjectModel } from '@nestjs/mongoose';
import { User } from './schemas/user.schema';
import { Model } from 'mongoose';
import * as bcrypt from 'bcrypt';
import { loginDataDto } from './dtos/loginData.Dto';
import { JwtService } from '@nestjs/jwt';
import { RefreshToken } from './schemas/refreshToken.schema';
import { v4 as uuidv4 } from 'uuid';
import { nanoid } from 'nanoid';
import { ResetToken } from './schemas/reset-token.schema';
import { MailService } from 'src/services/mail.service';

@Injectable()
export class AuthService {
  constructor(
    @InjectModel(User.name)
    private readonly userModel: Model<User>,
    @InjectModel(RefreshToken.name)
    private readonly refreshTokenModel: Model<RefreshToken>,
    @InjectModel(ResetToken.name)
    private readonly resetTokenModel: Model<ResetToken>,
    private readonly jwtService: JwtService,
    private readonly mailService: MailService,
  ) {}

  async signUp(signUpData: signUpDataDto) {
    const existingUser = await this.userModel.findOne({
      email: signUpData.email,
    });
    if (existingUser) {
      throw new BadRequestException('User with given email already exists');
    }

    if (signUpData.password !== signUpData.confirmPassword) {
      throw new BadRequestException(
        'Password and Confirm Password do not match',
      );
    }
    let hashedPassword: string = await bcrypt.hash(signUpData.password, 10);
    await this.userModel.create({
      email: signUpData.email,
      password: hashedPassword,
      name: signUpData.name,
    });
  }

  async login(credentials: loginDataDto) {
    const user = await this.userModel.findOne({ email: credentials.email });
    if (!user) {
      throw new BadRequestException('Invalid email or password');
    }

    const isPasswordMatching = await bcrypt.compare(
      credentials.password,
      user.password,
    );
    if (!isPasswordMatching) {
      throw new BadRequestException('Invalid email or password');
    }

    const tokens = await this.generateTokens(user._id);
    return {
      ...tokens,
      userId: user._id,
    };
  }

  async refreshTokens(refreshToken: string) {
    const storedToken = await this.refreshTokenModel.findOne({
      token: refreshToken,
      expiryDate: { $gt: new Date() },
    });
    if (!storedToken) {
      throw new UnauthorizedException();
    }

    return this.generateTokens(storedToken.userId);
  }

  async generateTokens(userId) {
    const accessToken = await this.jwtService.sign(
      { userId },
      { expiresIn: '1h' },
    );
    const refreshToken = uuidv4();

    await this.storeRefreshToken(refreshToken, userId);
    return { accessToken, refreshToken };
  }

  async storeRefreshToken(token: string, userId: string) {
    const expiryDate = new Date();
    expiryDate.setDate(expiryDate.getDate() + 3); // Set expiry date to 3 days from now

    await this.refreshTokenModel.updateOne(
      {
        userId,
      },
      {
        $set: { expiryDate, token },
      },
      {
        upsert: true,
      },
    );
  }

  async changePassword(
    userId: string,
    oldPassword: string,
    newPassword: string,
  ) {
    console.log('Changing password for userId:', userId);
    const user = await this.userModel.findById(userId);
    if (!user) {
      throw new BadRequestException('User not found');
    }

    const isMatch = await bcrypt.compare(oldPassword, user.password);
    if (!isMatch) {
      throw new BadRequestException('Old password is incorrect');
    }

    if (oldPassword === newPassword) {
      throw new BadRequestException('New password must be different');
    }

    const hashed = await bcrypt.hash(newPassword, 10);
    await this.userModel.updateOne(
      { _id: userId },
      { $set: { password: hashed } },
    );

    return { message: 'Password changed successfully' };
  }

  async forgotPassword(email: string) {
    const user = await this.userModel.findOne({ email });

    if (user) {
      const resetToken = nanoid(64);
      const expiryDate = new Date(Date.now() + 3600 * 1000); // 1 hour expiry
      await this.resetTokenModel.create({
        token: resetToken,
        userId: user._id,
        expiryDate,
      });
      await this.mailService.sendPasswordResetEmail(email, resetToken);
      return { message: 'Password resetmail sent' };
    } else {
      throw new BadRequestException('User with given email does not exist');
    }
  }

  async resetPassword(newPassword: string, resetToken: string) {
    const token = await this.resetTokenModel.findOne({
      token: resetToken,
      expiryDate: { $gt: new Date() },
    });
    if (!token) {
      throw new BadRequestException('Invalid or expired reset token');
    }

    const hashedPassword = await bcrypt.hash(newPassword, 10);
    await this.userModel.updateOne(
      { _id: token.userId },
      { $set: { password: hashedPassword } },
    );
    await this.resetTokenModel.deleteOne({ _id: token._id });

    return { message: 'Password reset successfully' };
  }

  async validateToken(token: string) {
    try {
      const payload = await this.jwtService.verifyAsync(token);
      const user = await this.userModel
        .findById(payload.userId)
        .select('-password');

      Logger.debug('Validated user:', user);
      if (!user) {
        throw new UnauthorizedException('Invalid token: user not found');
      }
      return { valid: true, user };
    } catch (error) {
      throw new UnauthorizedException('Invalid or expired token');
    }
  }

  async getMe(userId: string) {
    if (!userId) throw new UnauthorizedException('User id missing');
    const user = await this.userModel.findById(userId).select('-password');
    if (!user) throw new BadRequestException('User not found');
    return user;
  }
}
