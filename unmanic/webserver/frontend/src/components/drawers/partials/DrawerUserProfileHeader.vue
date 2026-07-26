<template>
  <div class="drawer-profile">
    <q-img
      src="~assets/bg-design-3.png"
      style="height: 90px">
      <div class="absolute-full profile-gradient"></div>

      <!-- BRANDING -->
      <div class="absolute-top bg-transparent q-pa-md row items-center">
        <q-img
          src="~assets/unmanic-logo-white.png"
          alt="Openmanic"
          width="32px"
          class="q-mr-sm"/>
        <div class="text-weight-bold">Openmanic</div>
      </div>
    </q-img>
  </div>
</template>

<script>

export default {
  name: 'DrawerUserProfileHeader',
}
</script>

<style>

.profile-gradient {
  background: linear-gradient(to bottom, var(--om-surface), rgba(24, 27, 33, 0.7)) !important;
}

</style>
