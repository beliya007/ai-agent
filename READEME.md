#### git新建仓库

```
git init
git remote add origin git@github.com:beliya007/你的仓库名.git

# 添加所有文件
git add .
# 提交备注
git commit -m "初始化项目代码"
# 推送主线（你习惯用master就写master，默认github主线是main）
git push -u origin master
```

#### 创建子分支

前提：保证你当前在 master 开发主线

##### 切换到master

```
git switch master
```

##### 拉取远程master最新代码，避免基线落后

```
git pull origin master
```

##### 基于master新建分支并直接切换进去

```
git switch -c feature/xxx master
```

##### 开发

```
git add .
git commit -m "完成首页布局逻辑"
git push -u origin feature/首页页面
```

##### 功能写完合并回父分支 master

```
//切回 master 主线
git switch master
git pull origin master
//合并子分支代码
git merge feature/首页页面
//推送更新后的 master 到远程
git push origin master
```

#### 