# Spring Boot

Learning guide for fast onboarding, code reading, and concept review.

## Core Concepts

Spring Boot 的核心思想是约定优于配置。通过自动装配机制，把常见工程化配置提前准备好，减少手工 wiring 的负担。

- `@SpringBootApplication`
- `@EnableAutoConfiguration`
- `@ComponentScan`
- `@Configuration`

## Key Features

内置 starter 体系让依赖和默认配置成组出现，能快速拉起 Web、Data、Actuator 等能力。

- starter dependencies
- auto configuration
- actuator
- profiles

## Project Structure

推荐把入口、配置、业务、基础设施按职责拆开，避免所有代码平铺在一个 package 下。

- `controller`
- `service`
- `repository`
- `config`

## Practical Checklist

第一次读 Spring Boot 项目时，不要先钻业务细节，先确认：

- main class 在哪里
- 自动配置生效路径
- profile 切换方式
- 配置文件来源
- actuator 是否开放

## Important Notes

真正提高开发速度的不是“魔法”，而是把重复配置模块化。理解自动装配边界，比背注解名字更重要。

## Sample Code

`@SpringBootApplication` 往往意味着以下三类职责被组合了：

- 配置类注册
- 组件扫描
- 自动配置启用
