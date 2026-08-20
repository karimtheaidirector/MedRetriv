/* ============================================================
   MedRetriv 3D WebGL Engine - ROBO v4.obj
   Robot Enhancements:
   A - Rich idle animations (head nod, shoulder bob, breathing)
   B - Full-screen eye/head tracking cursor
   C - Holographic scan line during searching state
   D - Particle burst/sparks on happy state
   E - Soft blob shadow on floor under robot
   ============================================================ */

window.MedBot3D = (function () {
  var scene, camera, renderer;
  var robotGroup, headGroup, hudRingMesh, particlesMesh;
  var keyLight, fillLight, rimLight, pointGlow;

  var eyeMeshes = [];
  var eyeMats = [];
  var state = 'idle';
  var isHovered = false;
  var clickPulse = 0;
  var lipSync = false;
  var lipSyncPhase = 0;

  // Mouth talking animation
  var mouthMesh = null;
  var mouthMat = null;
  var mouthScaleY = 0.08;
  var targetMouthScaleY = 0.08;

  // Blink Physics
  var blinkTimer = 0;
  var eyeScaleY = 1.0;
  var targetEyeScaleY = 1.0;

  // ── Enhancement A: Idle Animation State ──
  var idleNodPhase = 0;
  var idleBreathPhase = 0;
  var idleShoulderPhase = 0;

  // ── Enhancement C: Holographic Scan Line ──
  var scanLineMesh = null;
  var scanLineMat = null;
  var scanLineActive = false;

  // ── Enhancement D: Happy Particle Burst ──
  var burstParticles = null;
  var burstActive = false;
  var burstTimer = 0;
  var burstPositions = null;
  var burstVelocities = null;

  // ── Enhancement E: Blob Shadow ──
  var blobShadowMesh = null;

  var mouse = { x: 0, y: 0, tx: 0, ty: 0 };
  var hwx = window.innerWidth / 2, hwy = window.innerHeight / 2;
  var clock = new THREE.Clock();

  var STATES = {
    idle:      { emoji: 'data:emoji', text: 'Dr. MedRetriv is ready' },
    typing:    { emoji: 'data:emoji', text: 'Dr. MedRetriv is listening...' },
    searching: { emoji: 'data:emoji', text: 'Searching 515 evidence chunks...' },
    happy:     { emoji: 'data:emoji', text: 'Grounded answer complete!' },
    caution:   { emoji: 'data:emoji', text: 'Insufficient evidence / Out of scope' },
    surprised: { emoji: 'data:emoji', text: 'Curious clinical focus' }
  };
  var STATE_EMOJIS = { idle:'robot', typing:'writing_hand', searching:'mag', happy:'sparkles', caution:'warning', surprised:'open_mouth' };
  var STATE_EMOJI_MAP = { idle:'🤖', typing:'✍️', searching:'🔍', happy:'✨', caution:'⚠️', surprised:'😮' };

  function init() {
    var canvas = document.getElementById('canvas3d');
    var cont   = document.getElementById('canvas-container');
    if (!canvas || !cont) return;

    var W = window.innerWidth;
    var H = window.innerHeight;

    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x030712, 0.02);

    camera = new THREE.PerspectiveCamera(38, W / H, 0.1, 300);
    camera.position.set(0, 0.2, 9.5);
    camera.lookAt(new THREE.Vector3(0, 0, 0));

    renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;

    // Lighting
    keyLight = new THREE.DirectionalLight(0xec4899, 1.8);
    keyLight.position.set(-6, 8, 8);
    keyLight.castShadow = true;
    scene.add(keyLight);

    fillLight = new THREE.DirectionalLight(0x00c4df, 1.5);
    fillLight.position.set(6, -2, 6);
    scene.add(fillLight);

    rimLight = new THREE.DirectionalLight(0x38bdf8, 2.5);
    rimLight.position.set(0, 5, -8);
    scene.add(rimLight);

    pointGlow = new THREE.PointLight(0x00f0ff, 4.0, 12);
    pointGlow.position.set(-3.2, 0.6, 3.5);
    scene.add(pointGlow);

    scene.add(new THREE.AmbientLight(0x152438, 1.2));

    buildGridFloor();
    buildHoloHUD();
    buildParticleDust();

    /* =========================================================================
       ROBOT POSITION CONTROL:
       X = left/right  (-3.2 = center of left half)
       Y = up/down     (0.65 = center of ring)
       Z = depth
       ========================================================================= */
    robotGroup = new THREE.Group();
    headGroup  = new THREE.Group();
    robotGroup.add(headGroup);
    robotGroup.scale.set(0.68, 0.68, 0.68);
    robotGroup.position.set(-2.85, 0.50, -1);
    scene.add(robotGroup);

    buildScanLine();       // Enhancement C
    buildBurstParticles(); // Enhancement D
    buildBlobShadow();     // Enhancement E

    loadRoboV4Mesh();

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('resize', onResize);
    canvas.addEventListener('click', onClickRobot);
    canvas.addEventListener('mouseenter', function () { isHovered = true; });
    canvas.addEventListener('mouseleave', function () { isHovered = false; });

    animate();
  }

  // ── Environment ───────────────────────────────────────────────────────────
  function buildGridFloor() {
    var floor = new THREE.Mesh(
      new THREE.PlaneGeometry(60, 60),
      new THREE.MeshStandardMaterial({ color: 0x030712, roughness: 0.18, metalness: 0.88, transparent: true, opacity: 0.85 })
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -3.2;
    floor.receiveShadow = true;
    scene.add(floor);

    var grid = new THREE.GridHelper(60, 40, 0xec4899, 0x00c4df);
    grid.position.y = -3.18;
    grid.material.transparent = true;
    grid.material.opacity = 0.35;
    scene.add(grid);
  }

  function buildHoloHUD() {
    hudRingMesh = new THREE.Mesh(
      new THREE.RingGeometry(2.8, 2.8, 64),
      new THREE.MeshBasicMaterial({ color: 0x00c4df, side: THREE.DoubleSide, transparent: true, opacity: 0.38, blending: THREE.AdditiveBlending })
    );
    hudRingMesh.position.set(-3.2, 0.4, -2.0);
    scene.add(hudRingMesh);
  }

  function buildParticleDust() {
    var N = 850, geo = new THREE.BufferGeometry();
    var pos = new Float32Array(N * 3), col = new Float32Array(N * 3);
    for (var i = 0; i < N; i++) {
      pos[i*3]   = (Math.random()-0.5)*55;
      pos[i*3+1] = (Math.random()-0.5)*35;
      pos[i*3+2] = (Math.random()-0.5)*28-4;
      var p = Math.random() > 0.6;
      col[i*3]=p?0.92:0; col[i*3+1]=p?0.28:0.77; col[i*3+2]=p?0.6:1.0;
    }
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('color',    new THREE.BufferAttribute(col, 3));
    particlesMesh = new THREE.Points(geo, new THREE.PointsMaterial({
      size: 0.065, vertexColors: true, transparent: true, opacity: 0.6,
      blending: THREE.AdditiveBlending, depthWrite: false
    }));
    scene.add(particlesMesh);
  }

  // ── Enhancement C: Holographic Scan Line ──────────────────────────────────
  function buildScanLine() {
    var geo = new THREE.BoxGeometry(2.2, 0.04, 0.06);
    scanLineMat = new THREE.MeshBasicMaterial({
      color: 0x00ffff, transparent: true, opacity: 0.0,
      blending: THREE.AdditiveBlending, depthWrite: false
    });
    scanLineMesh = new THREE.Mesh(geo, scanLineMat);
    scanLineMesh.position.set(-2.85, -3.0, 0.5);
    scene.add(scanLineMesh);
  }

  // ── Enhancement D: Happy Particle Burst ──────────────────────────────────
  function buildBurstParticles() {
    var N = 120;
    var geo = new THREE.BufferGeometry();
    burstPositions  = new Float32Array(N * 3);
    burstVelocities = [];
    var col = new Float32Array(N * 3);

    for (var i = 0; i < N; i++) {
      burstPositions[i*3]   = 0;
      burstPositions[i*3+1] = 0;
      burstPositions[i*3+2] = 0;
      burstVelocities.push({
        x: (Math.random()-0.5)*4.5,
        y: Math.random()*5.0 + 1.0,
        z: (Math.random()-0.5)*3.0
      });
      // Mix cyan, green, gold colours
      var r = Math.random();
      if (r < 0.4) { col[i*3]=0;    col[i*3+1]=1;    col[i*3+2]=0.64; } // cyan-green
      else if (r < 0.7) { col[i*3]=1; col[i*3+1]=0.85; col[i*3+2]=0; }  // gold
      else { col[i*3]=0.6; col[i*3+1]=1; col[i*3+2]=0.6; }               // lime
    }
    geo.setAttribute('position', new THREE.BufferAttribute(burstPositions, 3));
    geo.setAttribute('color',    new THREE.BufferAttribute(col, 3));

    burstParticles = new THREE.Points(geo, new THREE.PointsMaterial({
      size: 0.14, vertexColors: true, transparent: true, opacity: 0,
      blending: THREE.AdditiveBlending, depthWrite: false
    }));
    scene.add(burstParticles);
  }

  function triggerBurst() {
    var rx = robotGroup.position.x;
    var ry = robotGroup.position.y;
    var rz = robotGroup.position.z;
    var N = burstPositions.length / 3;
    for (var i = 0; i < N; i++) {
      burstPositions[i*3]   = rx;
      burstPositions[i*3+1] = ry + 0.5;
      burstPositions[i*3+2] = rz;
    }
    burstParticles.geometry.attributes.position.needsUpdate = true;
    burstParticles.material.opacity = 1.0;
    burstActive = true;
    burstTimer  = 0;
  }

  // ── Enhancement E: Blob Shadow ────────────────────────────────────────────
  function buildBlobShadow() {
    blobShadowMesh = new THREE.Mesh(
      new THREE.CircleGeometry(1.1, 32),
      new THREE.MeshBasicMaterial({
        color: 0x000000, transparent: true, opacity: 0.35,
        depthWrite: false, blending: THREE.MultiplyBlending
      })
    );
    blobShadowMesh.rotation.x = -Math.PI / 2;
    blobShadowMesh.position.set(-2.85, -3.15, -1);
    scene.add(blobShadowMesh);
  }

  // ── OBJ Loader ────────────────────────────────────────────────────────────
  function loadRoboV4Mesh() {
    if (typeof THREE.OBJLoader === 'undefined') {
      buildProceduralFallback(); return;
    }
    var loader = new THREE.OBJLoader();
    loader.load('models/ROBO%20v4.obj', function (obj) {
      console.log('ROBO v4.obj loaded!');

      var bodyMat = new THREE.MeshStandardMaterial({ color: 0xd8e4f0, roughness: 0.18, metalness: 0.88 });
      var darkJointMat = new THREE.MeshStandardMaterial({ color: 0x08101d, roughness: 0.28, metalness: 0.92 });
      var darkVisorMat = new THREE.MeshStandardMaterial({ color: 0x02060f, roughness: 0.05, metalness: 0.96 });
      var emissiveAccentMat = new THREE.MeshStandardMaterial({ color: 0x00c4df, emissive: new THREE.Color(0x00c4df), emissiveIntensity: 1.2 });
      var eyeMat = new THREE.MeshStandardMaterial({ color: 0x00ffff, emissive: new THREE.Color(0x00f0ff), emissiveIntensity: 2.8, roughness: 0.05 });

      var modelPivot = new THREE.Group();
      modelPivot.add(obj);
      obj.rotation.x = -Math.PI / 2;
      obj.updateMatrixWorld(true);

      eyeMeshes = []; eyeMats = [];

      obj.traverse(function (child) {
        if (!child.isMesh) return;
        child.castShadow = true;
        child.receiveShadow = true;
        var fn  = (child.name + ' ' + (child.parent ? child.parent.name : '')).toLowerCase();
        var vc  = child.geometry.attributes.position ? child.geometry.attributes.position.count : 0;
        if (fn.includes('plane') || fn.includes('visor') || fn.includes('face') || fn.includes('screen')) {
          child.material = darkVisorMat;
        } else if (fn.includes('body25') || fn.includes('body26') || fn.includes('body40') || fn.includes('body41') || (vc >= 750 && vc <= 800)) {
          child.material = eyeMat;
          eyeMeshes.push(child); eyeMats.push(eyeMat);
        } else if (fn.includes('joint') || fn.includes('dark') || fn.includes('black')) {
          child.material = darkJointMat;
        } else if (fn.includes('accent') || fn.includes('line') || fn.includes('light')) {
          child.material = emissiveAccentMat;
        } else {
          child.material = bodyMat;
        }
      });

      console.log('Eye meshes:', eyeMeshes.length);

      var box    = new THREE.Box3().setFromObject(modelPivot);
      var center = box.getCenter(new THREE.Vector3());
      var size   = box.getSize(new THREE.Vector3());
      var scale  = 4.4 / (Math.max(size.x, size.y, size.z) || 1);
      modelPivot.scale.set(scale, scale, scale);
      modelPivot.position.set(-center.x * scale, -center.y * scale, -center.z * scale);
      headGroup.add(modelPivot);

      createMouthMesh();
    }, undefined, function (err) {
      console.error('OBJ load error:', err);
      buildProceduralFallback();
    });
  }

  // ── Talking Mouth ─────────────────────────────────────────────────────────
  function createMouthMesh() {
    mouthMat = new THREE.MeshStandardMaterial({
      color: 0x00f0ff, emissive: new THREE.Color(0x00f0ff), emissiveIntensity: 1.8, roughness: 0.1
    });
    mouthMesh = new THREE.Mesh(new THREE.BoxGeometry(0.52, 0.13, 0.06), mouthMat);
    mouthMesh.scale.set(1, 0.08, 1);

    if (eyeMeshes.length >= 2) {
      headGroup.updateMatrixWorld(true);
      var ec = new THREE.Vector3();
      for (var ei = 0; ei < eyeMeshes.length; ei++) {
        var wp = new THREE.Vector3();
        eyeMeshes[ei].getWorldPosition(wp);
        ec.add(wp);
      }
      ec.divideScalar(eyeMeshes.length);
      headGroup.worldToLocal(ec);
      mouthMesh.position.set(ec.x, ec.y - 0.45, ec.z + 0.05);
    } else {
      mouthMesh.position.set(0, 0.82, 1.05);
    }
    headGroup.add(mouthMesh);
  }

  // ── Procedural Fallback ───────────────────────────────────────────────────
  function buildProceduralFallback() {
    var silverMat = new THREE.MeshStandardMaterial({ color: 0xdce8f5, roughness: 0.18, metalness: 0.82 });
    var helmet = new THREE.Mesh(new THREE.SphereGeometry(1.4, 64, 64), silverMat);
    helmet.scale.set(1.0, 0.96, 0.94);
    headGroup.add(helmet);

    var fMat = new THREE.MeshStandardMaterial({ color: 0x00f0ff, emissive: new THREE.Color(0x00f0ff), emissiveIntensity: 2.8 });
    var eL = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.35, 0.1), fMat);
    eL.position.set(-0.4, 0.1, 1.3); headGroup.add(eL); eyeMeshes.push(eL); eyeMats.push(fMat);
    var eR = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.35, 0.1), fMat);
    eR.position.set(0.4, 0.1, 1.3); headGroup.add(eR); eyeMeshes.push(eR); eyeMats.push(fMat);

    var body = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 1.1, 2.2, 40), silverMat);
    body.position.set(0, -1.1, 0); robotGroup.add(body);
    headGroup.position.set(0, 1.4, 0);
    createMouthMesh();
  }

  // ── Input ─────────────────────────────────────────────────────────────────
  function onMouseMove(e) {
    // Enhancement B: full-screen cursor tracking (not clamped to canvas)
    mouse.tx = (e.clientX - hwx) / hwx;   // -1 → +1 range
    mouse.ty = (e.clientY - hwy) / hwy;
  }

  function onClickRobot() {
    setRobotState(state === 'surprised' ? 'happy' : 'surprised');
    clickPulse = 1.0;
    setTimeout(function () { if (state === 'surprised') setRobotState('idle'); }, 1800);
  }

  function onResize() {
    var w = window.innerWidth, h = window.innerHeight;
    hwx = w / 2; hwy = h / 2;
    if (camera && renderer) {
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    }
  }

  // ── Main Animation Loop ───────────────────────────────────────────────────
  function animate() {
    requestAnimationFrame(animate);
    var delta = clock.getDelta();
    var t     = clock.getElapsedTime();

    // Enhancement B: smooth eye/head tracking toward cursor anywhere on screen
    mouse.x += (mouse.tx - mouse.x) * 0.05;
    mouse.y += (mouse.ty - mouse.y) * 0.05;

    // ── Enhancement A: Idle Animations ──────────────────────────────
    var isHappy     = (state === 'happy');
    var isSearching = (state === 'searching');
    var isIdle      = (state === 'idle' || state === 'neutral');

    // Breathing cycle: slow sine on Y (0.8Hz)
    var breathY = Math.sin(t * 0.8 * Math.PI * 2) * 0.035;
    // Head gentle nod: very slow (0.3Hz), only in idle
    var nodX = isIdle ? Math.sin(t * 0.3 * Math.PI * 2) * 0.025 : 0;
    // Shoulder bob: slight Z rotation (0.6Hz), only idle
    var shoulderZ = isIdle ? Math.sin(t * 0.6 * Math.PI * 2) * 0.012 : 0;

    // Happy bounce (faster)
    var hoverOffset = isHappy
      ? Math.sin(t * 6.5) * 0.18
      : (isHovered ? Math.sin(t * 2.8) * 0.14 : breathY + Math.sin(t * 1.8) * 0.04);

    clickPulse *= 0.92;
    var pulseOffset = Math.sin(clickPulse * Math.PI * 4) * clickPulse * 0.2;

    // Lip-sync body bounce
    var lipOffset = lipSync ? Math.sin(lipSyncPhase) * 0.055 : 0;
    lipSyncPhase += delta * 18;

    if (robotGroup && headGroup) {
      robotGroup.position.y = 0.65 + hoverOffset + pulseOffset + lipOffset;

      // Enhancement A: apply idle shoulder bob to robot group Z rotation
      robotGroup.rotation.z = THREE.MathUtils.lerp(robotGroup.rotation.z, shoulderZ, 0.08);

      var tilt = (state === 'surprised') ? 0.18 : (state === 'typing' ? -0.08 : nodX);

      // Enhancement B: head tracking uses full screen -1..1 range
      if (state === 'caution') {
        headGroup.rotation.y = Math.sin(t * 14) * 0.26;
      } else {
        // Scale mouse.x (now -1..+1) to ±0.45 radians head turn
        headGroup.rotation.y = THREE.MathUtils.lerp(headGroup.rotation.y, mouse.x * 0.45, 0.07);
      }
      headGroup.rotation.x = THREE.MathUtils.lerp(headGroup.rotation.x, mouse.y * 0.25 + tilt, 0.07);
      headGroup.rotation.z = THREE.MathUtils.lerp(headGroup.rotation.z, shoulderZ * 0.6, 0.1);
    }

    // Enhancement E: Blob shadow scales/fades with height
    if (blobShadowMesh) {
      var heightAboveFloor = (robotGroup.position.y - (-3.15)) * 0.68; // account for group scale
      var shadowScale = THREE.MathUtils.clamp(1.4 - heightAboveFloor * 0.08, 0.6, 1.4);
      var shadowOpacity = THREE.MathUtils.clamp(0.38 - heightAboveFloor * 0.02, 0.1, 0.38);
      blobShadowMesh.scale.setScalar(shadowScale);
      blobShadowMesh.material.opacity = shadowOpacity;
      blobShadowMesh.position.x = robotGroup.position.x;
      blobShadowMesh.position.z = robotGroup.position.z;
    }

    // Enhancement C: Holographic scan line during searching
    if (scanLineMesh) {
      if (isSearching) {
        // Sweep from bottom to top of robot
        var scanY = ((t * 0.9) % 1.0) * 5.5 - 3.0;
        scanLineMesh.position.y = scanY;
        scanLineMesh.position.x = robotGroup.position.x;
        scanLineMesh.position.z = robotGroup.position.z + 0.5;
        scanLineMat.opacity = 0.55 + Math.sin(t * 12) * 0.15;
        scanLineMesh.scale.x = 1.0 + Math.sin(t * 8) * 0.08;
        scanLineMat.color.setHex(0x00ffff);
        scanLineActive = true;
      } else {
        scanLineMat.opacity = THREE.MathUtils.lerp(scanLineMat.opacity, 0, 0.12);
      }
    }

    // Enhancement D: Happy particle burst
    if (burstParticles) {
      if (burstActive) {
        burstTimer += delta;
        var N = burstPositions.length / 3;
        var gravity = -4.5;
        for (var bi = 0; bi < N; bi++) {
          burstVelocities[bi].y += gravity * delta;
          burstPositions[bi*3]   += burstVelocities[bi].x * delta;
          burstPositions[bi*3+1] += burstVelocities[bi].y * delta;
          burstPositions[bi*3+2] += burstVelocities[bi].z * delta;
        }
        burstParticles.geometry.attributes.position.needsUpdate = true;
        // Fade out over 1.8 seconds
        burstParticles.material.opacity = Math.max(0, 1.0 - burstTimer / 1.8);
        if (burstTimer > 1.8) {
          burstActive = false;
          burstParticles.material.opacity = 0;
          // Reset velocities for next burst
          for (var bj = 0; bj < N; bj++) {
            burstVelocities[bj].x = (Math.random()-0.5)*4.5;
            burstVelocities[bj].y = Math.random()*5.0+1.0;
            burstVelocities[bj].z = (Math.random()-0.5)*3.0;
          }
        }
      }
    }

    // ── Mouth Animation ──────────────────────────────────────────────
    if (mouthMesh) {
      if (lipSync) {
        var sw = Math.abs(Math.sin(t * 9.5)) * 0.55
               + Math.abs(Math.sin(t * 17.3)) * 0.25
               + Math.abs(Math.sin(t * 5.1)) * 0.20;
        targetMouthScaleY = 0.08 + sw * 0.92;
        mouthMat.emissiveIntensity = 2.2 + sw * 1.4;
        mouthMat.emissive.setHex(0x00f0ff);
      } else {
        targetMouthScaleY = 0.08;
        mouthMat.emissiveIntensity = THREE.MathUtils.lerp(mouthMat.emissiveIntensity, 0.6, 0.08);
      }
      mouthScaleY = THREE.MathUtils.lerp(mouthScaleY, targetMouthScaleY, 0.22);
      mouthMesh.scale.y = mouthScaleY;
    }

    // ── Blink Physics ────────────────────────────────────────────────
    blinkTimer += delta;
    if (blinkTimer > 3.6) {
      targetEyeScaleY = 0.06;
      if (blinkTimer > 3.78) { blinkTimer = 0; targetEyeScaleY = 1.0; }
    } else {
      targetEyeScaleY = 1.0;
    }
    eyeScaleY = THREE.MathUtils.lerp(eyeScaleY, targetEyeScaleY, 0.28);

    // ── Eye Expression Colors ────────────────────────────────────────
    for (var m = 0; m < eyeMats.length; m++) {
      var em = eyeMats[m];
      if (state === 'idle' || state === 'neutral') {
        em.color.setHex(0x00f0ff);
        em.emissive.setHex(0x00f0ff);
        em.emissiveIntensity = isHovered ? 2.8 : 2.0;
      } else if (state === 'typing') {
        // Glowing Magenta Typing State (0xff007f)
        em.color.setHex(0xff007f);
        em.emissive.setHex(0xff007f);
        em.emissiveIntensity = 3.6 + Math.sin(t * 16) * 1.4;
      } else if (state === 'happy') {
        // Emerald Green Answer Complete (0x00ffa3)
        em.color.setHex(0x00ffa3);
        em.emissive.setHex(0x00ffa3);
        em.emissiveIntensity = 3.8;
      } else if (state === 'surprised') {
        // Sky Blue (0x00a2ff)
        em.color.setHex(0x00a2ff);
        em.emissive.setHex(0x00a2ff);
        em.emissiveIntensity = 3.8;
      } else if (state === 'searching') {
        // Processing Cyan (0x00ffff)
        em.color.setHex(0x00ffff);
        em.emissive.setHex(0x00ffff);
        em.emissiveIntensity = 2.5 + Math.sin(t * 8) * 0.9;
      } else if (state === 'caution') {
        // Amber-Red Refusal Warning (0xff3300)
        em.color.setHex(0xff3300);
        em.emissive.setHex(0xff3300);
        em.emissiveIntensity = 3.5;
      }
    }


    // ── Eye Scale per Expression ─────────────────────────────────────
    for (var i = 0; i < eyeMeshes.length; i++) {
      var sx = (state === 'surprised') ? 1.35 : 1.0;
      var sy = (state === 'happy') ? 0.65 : (state === 'surprised' ? 1.25 : 1.0);
      eyeMeshes[i].scale.y = eyeScaleY * sy;
      eyeMeshes[i].scale.x = sx;
    }

    // Hover glow
    if (pointGlow) {
      pointGlow.intensity = THREE.MathUtils.lerp(pointGlow.intensity,
        (isHovered ? 5.5 : 3.8) + Math.sin(t*3)*0.6, 0.1);
    }

    if (hudRingMesh) hudRingMesh.rotation.z = t * 0.4;
    if (particlesMesh) {
      particlesMesh.rotation.y = t * 0.016 + mouse.x * 0.22;
      particlesMesh.rotation.x = mouse.y * 0.12;
    }

    renderer.render(scene, camera);
  }

  // ── Public API ────────────────────────────────────────────────────────────
  function setRobotState(s) {
    if (!STATES[s]) return;
    state = s;
    var e  = document.getElementById('robot-emoji');
    var tx = document.getElementById('robot-state-text');
    if (e)  e.textContent  = STATE_EMOJI_MAP[s] || '🤖';
    if (tx) tx.textContent = STATES[s].text;

    // Enhancement D: fire burst when answer found
    if (s === 'happy' && burstParticles) triggerBurst();
  }

  function setLipSync(active) {
    lipSync = !!active;
    for (var i = 0; i < eyeMats.length; i++) {
      eyeMats[i].emissiveIntensity = active ? 4.2 : 2.4;
    }
  }

  return { init: init, setRobotState: setRobotState, setLipSync: setLipSync };
})();

document.addEventListener('DOMContentLoaded', function () {
  window.MedBot3D.init();
});
