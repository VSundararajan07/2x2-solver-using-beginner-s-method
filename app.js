import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const FACE_ORDER = ['U', 'L', 'F', 'R', 'B', 'D'];
const COLORS = {
  W: { css: '#f4f4ee', name: 'White' },
  Y: { css: '#ffd83d', name: 'Yellow' },
  G: { css: '#26c878', name: 'Green' },
  B: { css: '#3784ff', name: 'Blue' },
  O: { css: '#ff963c', name: 'Orange' },
  R: { css: '#ff5364', name: 'Red' },
};
const SOLVED = { U:'Y', D:'W', F:'G', B:'B', R:'O', L:'R' };
const els = Object.fromEntries(['faces','resetBtn','solveBtn','status','stepBadge','currentMove','currentStage','startBtn','prevBtn','playBtn','nextBtn','endBtn','stepSlider','stepCount','speedSlider','speedValue','stageList','canvasWrap','canvasEmpty','cubeCanvas'].map(id=>[id,document.getElementById(id)]));
let result = null, current = 0, playing = false, timer = null;
let scene, camera, renderer, controls, stickerMeshes = [], resizeObserver;

function buildInputs() {
  els.faces.innerHTML = '';
  for (const face of FACE_ORDER) {
    const card = document.createElement('div');
    card.className = 'face-card';
    const title = document.createElement('div');
    title.className = 'face-title'; title.textContent = face;
    const cells = document.createElement('div'); cells.className = 'face-cells';
    for (let i=0;i<4;i++) {
      const select = document.createElement('select');
      select.className = 'color-select';
      select.setAttribute('aria-label', `${face} face sticker ${i+1}`);
      select.dataset.face = face; select.dataset.index = String(i);
      for (const [letter, color] of Object.entries(COLORS)) {
        const option = document.createElement('option');
        option.value = letter; option.textContent = letter; option.title = color.name;
        select.appendChild(option);
      }
      select.value = SOLVED[face];
      select.addEventListener('change', updateSelectColor);
      cells.appendChild(select);
    }
    card.append(title,cells); els.faces.appendChild(card);
  }
  refreshSelectColors();
}

function updateSelectColor(target) {
  const select = target.currentTarget || target;
  const color = COLORS[select.value];

  if (!color) return;

  select.style.background = color.css;
  select.style.color = select.value === 'W' ? '#222' : '#171528';
}

function refreshSelectColors() {
  els.faces.querySelectorAll('select').forEach(select => {
    updateSelectColor(select);
  });
}
function readFaces() {
  const faces={};
  for (const face of FACE_ORDER) {
    const values=[...els.faces.querySelectorAll(`select[data-face="${face}"]`)].map(el=>el.value);
    faces[face]=[values.slice(0,2),values.slice(2,4)];
  }
  return faces;
}
function solvedFaces(){const faces={};for(const f of FACE_ORDER)faces[f]=[[SOLVED[f],SOLVED[f]],[SOLVED[f],SOLVED[f]]];return faces;}
function setStatus(text,type=''){els.status.textContent=text;els.status.className=`status ${type}`;}

function faceGridPosition(face,row,col) {
  const left=col===0, top=row===0;
  const y=top?1:-1;
  if(face==='F')return [left?-1:1,y,1];
  if(face==='B')return [left?1:-1,y,-1];
  if(face==='R')return [1,y,left?1:-1];
  if(face==='L')return [-1,y,left?-1:1];
  const x=left?-1:1;
  if(face==='U')return [x,1,top?-1:1];
  return [x,-1,top?1:-1];
}
function faceNormal(face) {
  return {U:[0,1,0],D:[0,-1,0],R:[1,0,0],L:[-1,0,0],F:[0,0,1],B:[0,0,-1]}[face];
}
function init3D() {
  scene = new THREE.Scene();
  
  camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100);
  camera.position.set(4.2, 3.1, 5.2);
  camera.lookAt(0, 0, 0);

  renderer = new THREE.WebGLRenderer({antialias:true,alpha:true});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  renderer.setSize(els.cubeCanvas.clientWidth||500,els.cubeCanvas.clientHeight||350);
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  els.cubeCanvas.appendChild(renderer.domElement);
  controls=new OrbitControls(camera,renderer.domElement);
  controls.enableDamping=true;controls.dampingFactor=.08;controls.minDistance=3.5;controls.maxDistance=8;
  scene.add(new THREE.AmbientLight(0xffffff,2.0));
  const light=new THREE.DirectionalLight(0xffffff,2.6);light.position.set(4,6,5);scene.add(light);
  const coreMat=new THREE.MeshStandardMaterial({color:0x11131b,roughness:.55,metalness:.05});
  for(let x of [-.5,.5])for(let y of [-.5,.5])for(let z of [-.5,.5]){
    const core=new THREE.Mesh(new THREE.BoxGeometry(.985,.985,.985),coreMat);
    core.position.set(x,y,z);scene.add(core);
  }
  const stickerGeo=new THREE.PlaneGeometry(.88,.88);
  for(const face of FACE_ORDER)for(let r=0;r<2;r++)for(let c=0;c<2;c++){
    const pos=faceGridPosition(face,r,c), normal=faceNormal(face);
    const center=pos.map((v,i)=>normal[i]!==0?normal[i]*1.002:v*.5);
    const mat=new THREE.MeshStandardMaterial({color:0xffffff,roughness:.4,metalness:0.0,side:THREE.DoubleSide});
    const mesh=new THREE.Mesh(stickerGeo,mat);
    mesh.position.set(...center);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1),new THREE.Vector3(...normal));
    mesh.userData={face,index:r*2+c};scene.add(mesh);stickerMeshes.push(mesh);
  }
  resizeObserver=new ResizeObserver(()=>resize3D());resizeObserver.observe(els.cubeCanvas);
  animate();
}
function resize3D(){
  if(!renderer||!camera)return;
  const w=Math.max(1,els.cubeCanvas.clientWidth),h=Math.max(1,els.cubeCanvas.clientHeight);
  camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);
}
function animate(){requestAnimationFrame(animate);if(controls)controls.update();if(renderer&&scene&&camera)renderer.render(scene,camera);}
function drawState(state){
  for(const mesh of stickerMeshes){
    const face=mesh.userData.face,index=mesh.userData.index;
    const color=state[face][Math.floor(index/2)][index%2];
    mesh.material.color.set(COLORS[color]?.css||'#777777');
  }
  els.canvasEmpty.style.display='none';
}
function stop(){playing=false;if(timer)clearTimeout(timer);timer=null;els.playBtn.innerHTML='▶ <span>Play</span>';}
function renderStages(){
  els.stageList.innerHTML='';
  if(!result||!result.stages.length){els.stageList.innerHTML='<div class="empty-stage">No moves needed — the cube is already solved.</div>';return;}
  for(const stage of result.stages){
    const div=document.createElement('div');div.className='stage-item';
    const name=document.createElement('div');name.className='stage-name';name.textContent=stage.name;
    const moves=document.createElement('div');moves.className='stage-moves';moves.textContent=stage.moves.join(' ');
    div.append(name,moves);div.dataset.stage=stage.name;els.stageList.appendChild(div);
  }
}
function showStep(index){
  if(!result)return;
  current=Math.max(0,Math.min(result.steps.length,index));
  drawState(result.states[current]);
  els.stepSlider.value=String(current);els.stepCount.textContent=`${current} / ${result.steps.length}`;
  if(current===0){els.stepBadge.textContent='START';els.currentMove.textContent='—';els.currentStage.textContent='Initial state';}
  else{
    const step=result.steps[current-1];els.stepBadge.textContent=`MOVE ${current}`;
    els.currentMove.textContent=step.move;els.currentStage.textContent=step.stage;
  }
  els.stageList.querySelectorAll('.stage-item').forEach(el=>el.classList.toggle('active',current>0&&el.dataset.stage===result.steps[current-1]?.stage));
  const atEnd=current===result.steps.length;
  if(atEnd&&result.solved){els.stepBadge.textContent='SOLVED';}
  els.startBtn.disabled=els.prevBtn.disabled=current===0;
  els.nextBtn.disabled=els.endBtn.disabled=atEnd;
}
function playTick(){
  if(!playing||!result)return;
  if(current>=result.steps.length){stop();return;}
  showStep(current+1);
  if(current>=result.steps.length){stop();return;}
  timer=setTimeout(playTick,Number(els.speedSlider.value));
}
async function solve(){
  stop();els.solveBtn.disabled=true;els.solveBtn.textContent='Solving…';setStatus('Checking the cube and generating your solution…');
  try{
    const response=await fetch('/api/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({faces:readFaces()})});
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||'Could not solve this cube.');
    result=data;current=0;
    els.stepSlider.min='0';els.stepSlider.max=String(result.steps.length);els.stepSlider.value='0';
    els.speedValue.textContent=`${(800/Number(els.speedSlider.value)).toFixed(1)}×`;
    renderStages();showStep(0);
    setStatus(result.alreadySolved?'This cube is already solved.':'Solution ready — follow the moves in order.', 'success');
  }catch(error){setStatus(error.message||'Something went wrong. Please check your colours and try again.','error');}
  finally{els.solveBtn.disabled=false;els.solveBtn.innerHTML='<span>✦</span> Find solution <span class="button-arrow">→</span>';}
}
els.solveBtn.addEventListener('click',solve);
els.resetBtn.addEventListener('click',()=>{stop();buildInputs();result=null;current=0;els.stageList.innerHTML='<div class="empty-stage">Your solution stages will appear here.</div>';els.stepSlider.max='0';els.stepSlider.value='0';els.stepCount.textContent='0 / 0';els.stepBadge.textContent='START';els.currentMove.textContent='—';els.currentStage.textContent='Waiting for cube';els.canvasEmpty.style.display='grid';setStatus('Cube reset to the solved colour scheme.');if(scene)drawState(solvedFaces());});
els.startBtn.addEventListener('click',()=>{stop();showStep(0)});
els.prevBtn.addEventListener('click',()=>{stop();showStep(current-1)});
els.nextBtn.addEventListener('click',()=>{stop();showStep(current+1)});
els.endBtn.addEventListener('click',()=>{stop();showStep(result?.steps.length||0)});
els.playBtn.addEventListener('click',()=>{if(!result||!result.steps.length)return;if(playing){stop();return;}if(current>=result.steps.length)showStep(0);playing=true;els.playBtn.innerHTML='Ⅱ <span>Pause</span>';timer=setTimeout(playTick,250);});
els.stepSlider.addEventListener('input',()=>{stop();showStep(Number(els.stepSlider.value))});
els.speedSlider.addEventListener('input',()=>{const factor=800/Number(els.speedSlider.value);els.speedValue.textContent=`${factor.toFixed(1)}×`;});
buildInputs();init3D();drawState(solvedFaces());
