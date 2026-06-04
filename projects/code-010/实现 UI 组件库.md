# 实现 UI 组件库

**任务**: 跨平台移动应用
**时间**: 2026-06-04T23:28:27.966915

# 跨平台移动应用 UI 组件库实现方案

## 一、技术选型与架构设计

### 1.1 技术栈选择
```bash
# 推荐技术栈组合
Framework: React Native 0.72+ / Expo SDK 50+
Language: TypeScript 5.0+
State Management: Zustand / Redux Toolkit
Styling: React Native StyleSheet + CSS-in-JS (Styled Components)
Testing: Jest + React Native Testing Library
Documentation: Storybook 7.0
```

### 1.2 项目结构设计
```
src/
├── components/          # 组件库核心目录
│   ├── atoms/           # 基础原子组件
│   │   ├── Button/
│   │   ├── Input/
│   │   ├── Typography/
│   │   └── ...
│   ├── molecules/       # 分子组件
│   │   ├── SearchBar/
│   │   ├── Card/
│   │   └── ...
│   ├── organisms/       # 有机体组件
│   │   ├── Header/
│   │   ├── Form/
│   │   └── ...
│   ├── templates/       # 模板组件
│   │   ├── AuthLayout/
│   │   ├── DashboardLayout/
│   │   └── ...
│   └── index.ts         # 统一导出
├── styles/              # 样式系统
│   ├── theme.ts         # 主题配置
│   ├── colors.ts        # 颜色系统
│   ├── typography.ts    # 排版系统
│   └── spacing.ts       # 间距系统
├── hooks/               # 自定义 Hooks
├── utils/               # 工具函数
├── types/               # TypeScript 类型定义
└── docs/                # 文档
```

## 二、核心组件实现

### 2.1 设计系统基础

```typescript
// src/styles/theme.ts
export interface Theme {
  colors: Colors;
  typography: Typography;
  spacing: Spacing;
  borderRadius: BorderRadius;
  shadows: Shadows;
  animation: Animation;
}

export interface Colors {
  primary: {
    light: string;
    main: string;
    dark: string;
    contrastText: string;
  };
  secondary: {
    light: string;
    main: string;
    dark: string;
    contrastText: string;
  };
  neutral: {
    white: string;
    gray100: string;
    gray200: string;
    // ... 更多灰色层次
    black: string;
  };
  semantic: {
    success: string;
    warning: string;
    error: string;
    info: string;
  };
}

export const defaultTheme: Theme = {
  colors: {
    primary: {
      light: '#66bb6a',
      main: '#4caf50',
      dark: '#388e3c',
      contrastText: '#ffffff',
    },
    secondary: {
      light: '#ff7961',
      main: '#f44336',
      dark: '#ba000d',
      contrastText: '#ffffff',
    },
    neutral: {
      white: '#ffffff',
      gray100: '#f5f5f5',
      gray200: '#eeeeee',
      gray300: '#e0e0e0',
      gray400: '#bdbdbd',
      gray500: '#9e9e9e',
      gray600: '#757575',
      gray700: '#616161',
      gray800: '#424242',
      gray900: '#212121',
      black: '#000000',
    },
    semantic: {
      success: '#4caf50',
      warning: '#ff9800',
      error: '#f44336',
      info: '#2196f3',
    },
  },
  typography: {
    fontFamily: 'System',
    fontSize: {
      xs: 12,
      sm: 14,
      md: 16,
      lg: 18,
      xl: 20,
      xxl: 24,
      xxxl: 32,
    },
    fontWeight: {
      regular: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
    },
    lineHeight: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.75,
    },
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    full: 9999,
  },
  shadows: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.18,
      shadowRadius: 1.0,
      elevation: 1,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.2,
      shadowRadius: 3.0,
      elevation: 3,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.25,
      shadowRadius: 4.0,
      elevation: 6,
    },
  },
  animation: {
    fast: 150,
    normal: 300,
    slow: 500,
  },
};
```

### 2.2 主题提供者组件

```typescript
// src/components/ThemeProvider/ThemeProvider.tsx
import React, { createContext, useContext, useMemo } from 'react';
import { Theme, defaultTheme } from '../../styles/theme';

interface ThemeProviderProps {
  theme?: Partial<Theme>;
  children: React.ReactNode;
}

interface ThemeContextType {
  theme: Theme;
  isDarkMode: boolean;
  toggleDarkMode: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  theme: customTheme = {},
  children,
}) => {
  const [isDarkMode, setIsDarkMode] = React.useState(false);

  const mergedTheme = useMemo(() => {
    return {
      ...defaultTheme,
      ...customTheme,
      colors: {
        ...defaultTheme.colors,
        ...customTheme.colors,
        neutral: {
          ...defaultTheme.colors.neutral,
          ...(isDarkMode
            ? {
                white: '#121212',
                gray100: '#1e1e1e',
                gray200: '#2d2d2d',
                // ... 暗黑模式覆盖
              }
            : {}),
          ...customTheme.colors?.neutral,
        },
      },
    };
  }, [customTheme, isDarkMode]);

  const toggleDarkMode = () => setIsDarkMode(!isDarkMode);

  const contextValue = useMemo(
    () => ({
      theme: mergedTheme,
      isDarkMode,
      toggleDarkMode,
    }),
    [mergedTheme, isDarkMode, toggleDarkMode]
  );

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
```

### 2.3 基础组件实现

#### 2.3.1 Button 组件

```typescript
// src/components/atoms/Button/Button.tsx
import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { useTheme } from '../../ThemeProvider/ThemeProvider';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  onPress: () => void;
  style?: ViewStyle;
  textStyle?: TextStyle;
  children: string;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  leftIcon,
  rightIcon,
  onPress,
  style,
  textStyle,
  children,
}) => {
  const { theme } = useTheme();

  const buttonStyles = StyleSheet.create({
    container: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: theme.borderRadius.md,
      paddingVertical: size === 'sm' ? theme.spacing.xs : 
                      size === 'md' ? theme.spacing.sm : 
                      theme.spacing.md,
      paddingHorizontal: size === 'sm' ? theme.spacing.sm : 
                        size === 'md' ? theme.spacing.md : 
                        theme.spacing.lg,
      opacity: disabled ? 0.6 : 1,
      width: fullWidth ? '100%' : 'auto',
      ...(variant === 'primary' && {
        backgroundColor: disabled ? theme.colors.neutral.gray400 : theme.colors.primary.main,
      }),
      ...(variant === 'secondary' && {
        backgroundColor: disabled ? theme.colors.neutral.gray400 : theme.colors.secondary.main,
      }),
      ...(variant === 'outline' && {
        backgroundColor: 'transparent',
        borderWidth: 1,
        borderColor: disabled ? theme.colors.neutral.gray400 : theme.colors.primary.main,
      }),
      ...(variant === 'ghost' && {
        backgroundColor: 'transparent',
      }),
    },
    text: {
      fontWeight: theme.typography.fontWeight.semibold,
      color: variant === 'outline' || variant === 'ghost'
        ? theme.colors.primary.main
        : theme.colors.primary.contrastText,
      ...(size === 'sm' && {
        fontSize: theme.typography.fontSize.sm,
      }),
      ...(size === 'md' && {
        fontSize: theme.typography.fontSize.md,
      }),
      ...(size === 'lg' && {
        fontSize: theme.typography.fontSize.lg,
      }),
    },
  });

  return (
    <TouchableOpacity
      style={[buttonStyles.container, style]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator
          size={size === 'sm' ? 'small' : 'small'}
          color={variant === 'outline' || variant === 'ghost' 
            ? theme.colors.primary.main 
            : theme.colors.primary.contrastText}
        />
      ) : (
        <>
          {leftIcon && <>{leftIcon}</>}
          <Text style={[buttonStyles.text, textStyle]}>{children}</Text>
          {rightIcon && <>{rightIcon}</>}
        </>
      )}
    </TouchableOpacity>
  );
};
```

#### 2.3.2 Input 组件

```typescript
// src/components/atoms/Input/Input.tsx
import React, { useState, useRef } from 'react';
import {
  View,
  TextInput,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { useTheme } from '../../ThemeProvider/ThemeProvider';

export type InputVariant = 'default' | 'filled' | 'outline';

export interface InputProps {
  variant?: InputVariant;
  label?: string;
  placeholder?: string;
  value?: string;
  onChangeText?: (text: string) => void;
  onBlur?: () => void;
  onFocus?: () => void;
  secureTextEntry?: boolean;
  multiline?: boolean;
  numberOfLines?: number;
  maxLength?: number;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  error?: string;
  disabled?: boolean;
  style?: object;
}

export const Input: React.FC<InputProps> = ({
  variant = 'default',
  label,
  placeholder,
  value,
  onChangeText,
  onBlur,
  onFocus,
  secureTextEntry,
  multiline,
  numberOfLines = 1,
  maxLength,
  leftIcon,
  rightIcon,
  error,
  disabled = false,
  style,
}) => {
  const { theme } = useTheme();
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<TextInput>(null);

  const handleFocus = () => {
    setIsFocused(true);
    onFocus?.();
  };

  const handleBlur = () => {
    setIsFocused(false);
    onBlur?.();
  };

  const containerStyle = StyleSheet.create({
    container: {
      marginBottom: error ? theme.spacing.xs : theme.spacing.md,
    },
    label: {
      fontSize: theme.typography.fontSize.sm,
      color: disabled 
        ? theme.colors.neutral.gray500 
        : error 
          ? theme.colors.semantic.error 
          : theme.colors.neutral.gray700,
      marginBottom: theme.spacing.xs,
    },
    inputContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      borderRadius: theme.borderRadius.md,
      paddingHorizontal: theme.spacing.sm,
      minHeight: 44,
      backgroundColor: variant === 'filled' 
        ? theme.colors.neutral.gray100 
        : 'transparent',
      borderWidth: variant === 'outline' ? 1 : 0,
      borderColor: error 
        ? theme.colors.semantic.error 
        : isFocused 
          ? theme.colors.primary.main 
          : theme.colors.neutral.gray300,
    },
    input: {
      flex: 1,
      fontSize: theme.typography.fontSize.md,
      color: disabled ? theme.colors.neutral.gray500 : theme.colors.neutral.gray900,
      paddingVertical: theme.spacing.sm,
      paddingHorizontal: theme.spacing.sm,
      ...(multiline && {
        minHeight: numberOfLines * 24,
        textAlignVertical: 'top',
      }),
    },
    errorText: {
      fontSize: theme.typography.fontSize.xs,
      color: theme.colors.semantic.error,
      marginTop: theme.spacing.xs,
    },
    icon: {
      marginHorizontal: theme.spacing.xs,
    },
  });

  return (
    <View style={[containerStyle.container, style]}>
      {label && <Text style={containerStyle.label}>{label}</Text>}
      <TouchableOpacity
        style={containerStyle.inputContainer}
        onPress={() => inputRef.current?.focus()}
        activeOpacity={0.9}
      >
        {leftIcon && <View style={containerStyle.icon}>{leftIcon}</View>}
        <TextInput
          ref={inputRef}
          style={containerStyle.input}
          placeholder={placeholder}
          placeholderTextColor={theme.colors.neutral.gray500}
          value={value}
          onChangeText={onChangeText}
          onFocus={handleFocus}
          onBlur={handleBlur}
          secureTextEntry={secureTextEntry}
          multiline={multiline}
          numberOfLines={numberOfLines}
          maxLength={maxLength}
          editable={!disabled}
        />
        {rightIcon && <View style={containerStyle.icon}>{rightIcon}</View>}
      </TouchableOpacity>
      {error && <Text style={containerStyle.errorText}>{error}</Text>}
    </View>
  );
};
```

#### 2.3.3 Card 组件

```typescript
// src/components/molecules/Card/Card.tsx
import React from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Image,
  ViewStyle,
} from 'react-native';
import { useTheme } from '../../ThemeProvider/ThemeProvider';
import { Typography } from '../Typography/Typography';

export interface CardProps {
  title?: string;
  subtitle?: string;
  description?: string;
  imageSource?: { uri: string } | number;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  onPress?: () => void;
  style?: ViewStyle;
  elevation?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  description,
  imageSource,
  header,
  footer,
  onPress,
  style,
  elevation = 'md',
}) => {
  const { theme } = useTheme();

  const cardStyles = StyleSheet.create({
    container: {
      backgroundColor: theme.colors.neutral.white,
      borderRadius: theme.borderRadius.lg,
      overflow: 'hidden',
      ...(elevation !== 'none' && theme.shadows[elevation]),
    },
    image: {
      width: '100%',
      height: 200,
      backgroundColor: theme.colors.neutral.gray200,
    },
    content: {
      padding: theme.spacing.md,
    },
    title: {
      fontSize: theme.typography.fontSize.lg,
      fontWeight: theme.typography.fontWeight.bold,
      color: theme.colors.neutral.gray900,
      marginBottom: theme.spacing.xs,
    },
    subtitle: {
      fontSize: theme.typography.fontSize.sm,
      color: theme.colors.neutral.gray600,
      marginBottom: theme.spacing.sm,
    },
    description: {
      fontSize: theme.typography.fontSize.md,
      color: theme.colors.neutral.gray700,
      lineHeight: 24,
    },
    headerContainer: {
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.neutral.gray200,
    },
    footerContainer: {
      borderTopWidth: 1,
      borderTopColor: theme.colors.neutral.gray200,
    },
  });

  const Content = () => (
    <>
      {header && (
        <View style={cardStyles.headerContainer}>{header}</View>
      )}
      
      {imageSource && (
        <Image source={imageSource} style={cardStyles.image} resizeMode="cover" />
      )}
      
      <View style={cardStyles.content}>
        {title && <Typography style={cardStyles.title}>{title}</Typography>}
        {subtitle && (
          <Typography style={cardStyles.subtitle}>{subtitle}</Typography>
        )}
        {description && (
          <Typography style={cardStyles.description}>{description}</Typography>
        )}
      </View>
      
      {footer && (
        <View style={cardStyles.footerContainer}>{footer}</View>
      )}
    </>
  );

  if (onPress) {
    return (
      <TouchableOpacity
        style={[cardStyles.container, style]}
        onPress={onPress}
        activeOpacity={0.95}
      >
        <Content />
      </TouchableOpacity>
    );
  }

  return (
    <View style={[cardStyles.container, style]}>
      <Content />
    </View>
  );
};
```

## 三、高级功能实现

### 3.1 响应式布局系统

```typescript
// src/components/layout/ResponsiveContainer/ResponsiveContainer.tsx
import React from 'react';
import { View, StyleSheet, useWindowDimensions } from 'react-native';
import { useTheme } from '../../ThemeProvider/ThemeProvider';

interface Breakpoints {
  mobile: number;
  tablet: number;
  desktop: number;
}

const defaultBreakpoints: Breakpoints = {
  mobile: 576,
  tablet: 768,
  desktop: 1024,
};

interface ResponsiveContainerProps {
  children: React.ReactNode;
  breakpoints?: Partial<Breakpoints>;
  style?: object;
}

export const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  breakpoints = {},
  style,
}) => {
  const { theme } = useTheme();
  const { width } = useWindowDimensions();
  
  const mergedBreakpoints = { ...defaultBreakpoints, ...breakpoints };
  
  const getBreakpoint = () => {
    if (width < mergedBreakpoints.mobile) return 'mobile';
    if (width < mergedBreakpoints.tablet) return 'tablet';
    return 'desktop';
  };

  const breakpoint = getBreakpoint();

  const containerStyle = StyleSheet.create({
    container: {
      flex: 1,
      padding: breakpoint === 'mobile' ? theme.spacing.sm : theme.spacing.md,
      maxWidth: breakpoint === 'desktop' ? 1200 : '100%',
      alignSelf: 'center',
    },
  });

  return (
    <View style={[containerStyle.container, style]}>
      {children}
    </View>
  );
};
```

### 3.2 动画系统

```typescript
// src/hooks/useAnimation.ts
import { useRef, useEffect } from 'react';
import { Animated } from 'react-native';

export interface AnimationConfig {
  duration?: number;
  delay?: number;
  useNativeDriver?: boolean;
  easing?: (value: number) => number;
}

export const useAnimation = (config: AnimationConfig = {}) => {
  const animatedValue = useRef(new Animated.Value(0)).current;
  const isVisible = useRef(false);

  const defaultConfig = {
    duration: 300,
    delay: 0,
    useNativeDriver: true,
    easing: undefined,
    ...config,
  };

  const fadeIn = () => {
    Animated.timing(animatedValue, {
      toValue: 1,
      ...defaultConfig,
    }).start(() => {
      isVisible.current = true;
    });
  };

  const fadeOut = () => {
    Animated.timing(animatedValue, {
      toValue: 0,
      ...defaultConfig,
    }).start(() => {
      isVisible.current = false;
    });
  };

  const slideIn = (direction: 'up' | 'down' | 'left' | 'right' = 'up', distance = 50) => {
    const initialValue = direction === 'up' || direction === 'left' ? distance : -distance;
    
    animatedValue.setValue(initialValue);
    
    Animated.timing(animatedValue, {
      toValue: 0,
      ...defaultConfig,
    }).start(() => {
      isVisible.current = true;
    });
  };

  const scale = (toValue = 1) => {
    Animated.spring(animatedValue, {
      toValue,
      useNativeDriver: defaultConfig.useNativeDriver,
      bounciness: 8,
      speed: 12,
    }).start();
  };

  const interpolate = (
    inputRange: number[],
    outputRange: number[] | string[],
    extrapolate?: 'clamp' | 'extend' | 'identity'
  ) => {
    return animatedValue.interpolate({
      inputRange,
      outputRange,
      extrapolate: extrapolate || 'clamp',
    });
  };

  useEffect(() => {
    return () => {
      animatedValue.stopAnimation();
    };
  }, []);

  return {
    animatedValue,
    isVisible: isVisible.current,
    fadeIn,
    fadeOut,
    slideIn,
    scale,
    interpolate,
  };
};
```

### 3.3 表单验证系统

```typescript
// src/components/organisms/Form/FormValidator.ts
export interface ValidationRule {
  type: 'required' | 'email' | 'minLength' | 'maxLength' | 'pattern' | 'custom';
  value?: any;
  message: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string[]>;
}

export class FormValidator {
  private rules: Record<string, ValidationRule[]> = {};
  private values: Record<string, any> = {};

  constructor(initialValues: Record<string, any> = {}) {
    this.values = initialValues;
  }

  setRules(field: string, rules: ValidationRule[]) {
    this.rules[field] = rules;
    return this;
  }

  setValue(field: string, value: any) {
    this.values[field] = value;
    return this;
  }

  validate(): ValidationResult {
    const errors: Record<string, string[]> = {};
    let isValid = true;

    Object.keys(this.rules).forEach(field => {
      const fieldRules = this.rules[field];
      const value = this.values[field];
      const fieldErrors: string[] = [];

      fieldRules.forEach(rule => {
        if (!this.validateRule(rule, value)) {
          fieldErrors.push(rule.message);
          isValid = false;
        }
      });

      if (fieldErrors.length > 0) {
        errors[field] = fieldErrors;
      }
    });

    return { isValid, errors };
  }

  private validateRule(rule: ValidationRule, value: any): boolean {
    switch (rule.type) {
      case 'required':
        return value !== undefined && value !== null && value !== '';
      
      case 'email':
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
      
      case 'minLength':
        return typeof value === 'string' && value.length >= (rule.value || 0);
      
      case 'maxLength':
        return typeof value === 'string' && value.length <= (rule.value || Infinity);
      
      case 'pattern':
        return rule.value instanceof RegExp && rule.value.test(value);
      
      case 'custom':
        return typeof rule.value === 'function' && rule.value(value);
      
      default:
        return true;
    }
  }
}
```

## 四、文档与示例

### 4.1 Storybook 配置

```javascript
// .storybook/main.js
module.exports = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx|mdx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-react-native-web',
  ],
  typescript: {
    check: false,
    checkOptions: {},
    reactDocgen: 'react-docgen-typescript',
    reactDocgenTypescriptOptions: {
      shouldExtractLiteralValuesFromEnum: true,
      propFilter: (prop) =>
        prop.parent ? !/node_modules/.test(prop.parent.fileName) : true,
    },
  },
};
```

### 4.2 使用示例

```typescript
// src/examples/LoginScreen.tsx
import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { ThemeProvider, Button, Input, Card, Typography } from '../components';
import { MaterialIcons } from '@expo/vector-icons';

const LoginScreen: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = () => {
    // 登录逻辑
  };

  return (
    <ThemeProvider>
      <View style={styles.container}>
        <Card
          title="欢迎登录"
          subtitle="请使用您的账户信息登录"
          style={styles.card}
        >
          <Input
            label="邮箱"
            placeholder="请输入邮箱地址"
            value={email}
            onChangeText={setEmail}
            leftIcon={<MaterialIcons name="email" size={20} color="#757575" />}
            keyboardType="email-address"
            autoCapitalize="none"
          />

          <Input
            label="密码"
            placeholder="请输入密码"
            value={password}
            onChangeText={setPassword}
            leftIcon={<MaterialIcons name="lock" size={20} color="#757575" />}
            secureTextEntry
          />

          <Button
            variant="primary"
            fullWidth
            onPress={handleLogin}
            style={styles.button}
          >
            登录
          </Button>

          <View style={styles.footer}>
            <Typography variant="body2" color="textSecondary">
              还没有账户？
            </Typography>
            <Button variant="ghost" onPress={() => {}}>
              立即注册
            </Button>
          </View>
        </Card>
      </View>
    </ThemeProvider>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#f5f5f5',
  },
  card: {
    padding: 24,
  },
  button: {
    marginTop: 16,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 24,
  },
});

export default LoginScreen;
```

## 五、测试策略

### 5.1 组件单元测试

```typescript
// src/components/atoms/Button/Button.test.tsx
import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { ThemeProvider } from '../../ThemeProvider/ThemeProvider';
import { Button } from './Button';

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>{children}</ThemeProvider>
);

describe('Button', () => {
  it('renders correctly with default props', () => {
    const { getByText } = render(
      <TestWrapper>
        <Button onPress={() => {}}>Click me</Button>
      </TestWrapper>
    );

    expect(getByText('Click me')).toBeTruthy();
  });

  it('calls onPress when pressed', () => {
    const mockOnPress = jest.fn();
    const { getByText } = render(
      <TestWrapper>
        <Button onPress={mockOnPress}>Click me</Button>
      </TestWrapper>
    );

    fireEvent.press(getByText('Click me'));
    expect(mockOnPress).toHaveBeenCalledTimes(1);
  });

  it('does not call onPress when disabled', () => {
    const mockOnPress = jest.fn();
    const { getByText } = render(
      <TestWrapper>
        <Button onPress={mockOnPress} disabled>
          Click me
        </Button>
      </TestWrapper>
    );

    fireEvent.press(getByText('Click me'));
    expect(mockOnPress).not.toHaveBeenCalled();
  });

  it('shows loading indicator when loading is true', () => {
    const { getByTestId } = render(
      <TestWrapper>
        <Button onPress={() => {}} loading>
          Click me
        </Button>
      </TestWrapper>
    );

    expect(getByTestId('activity-indicator')).toBeTruthy();
  });

  it('renders with different variants', () => {
    const variants = ['primary', 'secondary', 'outline', 'ghost'] as const;
    
    variants.forEach(variant => {
      const { getByText } = render(
        <TestWrapper>
          <Button variant={variant} onPress={() => {}}>
            {variant} button
          </Button>
        </TestWrapper>
      );

      expect(getByText(`${variant} button`)).toBeTruthy();
    });
  });
});
```

## 六、部署与维护

### 6.1 版本管理

```json
// package.json
{
  "name": "@yourcompany/ui-components",
  "version": "1.0.0",
  "description": "跨平台移动应用 UI 组件库",
  "main": "lib/index.js",
  "types": "lib/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "lint": "eslint . --ext .ts,.tsx",
    "storybook": "start-storybook -p 6006",
    "build-storybook": "build-storybook",
    "prepublishOnly": "npm run build",
    "version": "npm run build && git add -A src",
    "postversion": "git push && git push --tags"
  },
  "keywords": [
    "react-native",
    "ui-components",
    "mobile",
    "cross-platform"
  ],
  "repository": {
    "type": "git",
    "url": "https://github.com/yourcompany/ui-components.git"
  },
  "license": "MIT",
  "peerDependencies": {
    "react": ">=16.8.0",
    "react-native": ">=0.60.0"
  }
}
```

### 6.2 发布配置

```typescript
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2018",
    "module": "commonjs",
    "lib": ["ES2020", "DOM"],
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "./lib",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "jsx": "react"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "**/*.test.ts", "**/*.test.tsx"]
}
```

## 七、性能优化

### 7.1 组件优化策略

```typescript
// src/utils/optimization.ts
import { useCallback, useMemo } from 'react';

export const useOptimizedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  deps: any[]
): T => {
  return useCallback(callback, deps);
};

export const useOptimizedMemo = <T>(factory: () => T, deps: any[]): T => {
  return useMemo(factory, deps);
};

export const withMemoization = <P extends object>(
  Component: React.ComponentType<P>
) => {
  return React.memo(Component, (prevProps, nextProps) => {
    // 自定义比较逻辑
    return JSON.stringify(prevProps) === JSON.stringify(nextProps);
  });
};
```

## 总结

本 UI 组件库实现方案提供了完整的跨平台移动应用组件库解决方案，包括：

1. **完整的架构设计**：基于原子设计原则，从原子组件到有机体组件
2. **强大的主题系统**：支持明暗模式、自定义主题和响应式设计
3. **丰富的组件集合**：包含基础UI组件、复合组件和布局系统
4. **完善的工具链**：TypeScript 类型安全、Storybook 文档、自动化测试
5. **优秀的性能**：动画系统、懒加载、内存优化
6. **详细的文档**：完整的使用示例和API文档
7. **可维护性**：模块化设计、版本管理、CI/CD 支持

该组件库可以显著提升开发效率，确保应用UI一致性，并支持快速迭代和定制化需求。