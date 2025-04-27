# 겜린더 백엔드 로컬 환경 코드

## Blog Post
[MongoDB는 겜린더에 적합한 DB일까?](https://velog.io/@grit_munhyeok/겜린더-백엔드-문제-인식과-문제-해결을-위한-조사)

[Redis를 이용해 겜린더 검색 자동완성 성능을 개선해 보기](https://velog.io/@grit_munhyeok/겜린더-검색-자동완성-성능을-개선해-보기)

## 실제 겜린더에 사용할 용도로 제작 중입니다.
## 프로덕션 repo는 Private 처리 되어있습니다.



## 최근 작업
리팩토링 game, search, user route에 있는 로직을 Service 로직으로 옮기기 

테스트 코드 작성하기 (작성 중)


## Server H/W
- Mini PC (Intel N100)
- ARM Arch는 ARMv8.2A 이상부터 지원하고 적절한 CPU 아키텍쳐가 없는 단일 보드 하드웨어를 지원하지 않는다. (라즈베리파이 지원 안함 😭) 자세한 부분은 [MongoDB 프로덕션 정보 참고](https://www.mongodb.com/ko-kr/docs/manual/administration/production-notes/)
  

## Specs
### Language
Python

### Web Framework
FastAPI

### DB
MongoDB
- pymongo

Redis
- redis-py


## Implementation
### Game
- Game Data Caching
- platform, tag filtering

### Search
- Autocomplete (검색어 자동완성)
- MongoDB Full Text Search & Redis Search Result Caching

### User
- JWT 기반 로그인 구현
- 회원가입 Email 인증 기능 구현
- device_id에 따른 refresh_token 생성 로직



Redis Caching
- Calendar Data
- GameInfo
- Search Result

## Caching Strategies
Look-Aside
![](/Readme%20Image/Caching%20Strategies.png)

## Architecture
![](/Readme%20Image/Back-End%20Architecture.png)

## Device ID-based refresh token generation
![](/Readme%20Image/generate%20refresh_token%20process.png)

## AutoComplete Sequence Diagram
![](/Readme%20Image/Autocomplete_Diagram.png)






