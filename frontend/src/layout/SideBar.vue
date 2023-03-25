<template>
  <el-scrollbar wrap-class="scrollbar-wrapper">
    <el-menu
      router
      text-color="#bfcbd9"
      active-text-color="rgb(64,158,255)"
      :default-active="$route.path"
      background-color="transparent"
    >
      <el-menu-item index="/">
        <el-icon><HomeFilled /></el-icon>首页
      </el-menu-item>
      <el-menu-item :index="$router.resolve({ name: 'svc' }).href">
        <el-icon><Refresh /></el-icon>SVC转换
      </el-menu-item>
      <el-menu-item index="/">
        <el-icon><RefreshRight /></el-icon>DiffSinger生成
      </el-menu-item>
      <el-menu-item :index="$router.resolve({ name: 'vm' }).href">
        <el-icon><EditPen /></el-icon>歌曲音声分离
      </el-menu-item>
      <a href="https://github.com/realerikk0/so-vits-svc-webui" target="_blank">
        <el-menu-item>
          <el-icon><Share /></el-icon>项目地址
        </el-menu-item>
      </a>
    </el-menu>
  </el-scrollbar>
</template>

<script>
export default {
  name: 'SideBar'
}
</script>
<style>
.scrollbar-wrapper .el-menu {
  border: none;
}
</style>
