const fs = require('fs');
const path = require('path');

// 1. Adaptado para Re-cicla2 (JS, JSON, HTML, CSS, Markdown)
const allowedExtensions = ['.js', '.jsx', '.ts', '.tsx', '.json', '.html', '.css', '.md'];

// 2. Carpetas y archivos prohibidos (¡Para no colapsar la IA ni subir credenciales!)
const ignoreDirs = [
  'node_modules', 
  '.git', 
  '__pycache__', 
  'venv', 
  'env', 
  '.firebase',       // Caché de Firebase
  'project_dump.md'  // Evita que el script se lea a sí mismo
];

// 3. Archivos específicos sensibles que JAMÁS deben entrar al dump por seguridad
const secretFiles = ['firebase_credentials.json', '.env'];

function generateTree(dir, prefix = '') {
  if (!fs.existsSync(dir)) return '';
  const entries = fs.readdirSync(dir);
  let tree = '';

  // Filtrar entradas ignoradas para que el conector "┗" se calcule correctamente
  const filteredEntries = entries.filter(entry => !ignoreDirs.includes(entry) && !secretFiles.includes(entry));

  filteredEntries.forEach((entry, index) => {
    const fullPath = path.join(dir, entry);
    const isLast = index === filteredEntries.length - 1;
    const connector = isLast ? '┗' : '┣';
    const subPrefix = prefix + (isLast ? '  ' : '┃ ');

    tree += `${prefix}${connector} ${entry}\n`;

    if (fs.statSync(fullPath).isDirectory()) {
      tree += generateTree(fullPath, subPrefix);
    }
  });
  return tree;
}

function walk(dir, fileList = []) {
  if (!fs.existsSync(dir)) return fileList;

  fs.readdirSync(dir).forEach(file => {
    // Si está en la lista de ignorados o secretos, saltar por completo
    if (ignoreDirs.includes(file) || secretFiles.includes(file)) return;

    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      walk(fullPath, fileList);
    } else {
      const ext = path.extname(fullPath);
      if (allowedExtensions.includes(ext)) {
        const content = fs.readFileSync(fullPath, 'utf8');
        // Obtener el lenguaje para el bloque de código de Markdown
        let lang = ext.slice(1);
        if (ext === '.jsx' || ext === '.tsx') lang = 'javascript';
        
        // Formatear la ruta relativa para que sea más legible en el reporte
        const relativePath = path.relative(__dirname, fullPath);

        fileList.push(`## 📄 Archivo: ${relativePath}\n\n\`\`\`${lang}\n${content}\n\`\`\`\n`);
      }
    }
  });
  return fileList;
}

// Escanea todo el proyecto desde la raíz del backend/proyecto
const targetPath = path.join(__dirname, '.');
console.log('Generando árbol de directorios...');
const tree = generateTree(targetPath);

console.log('Leyendo contenido de archivos permitidos...');
const files = walk(targetPath);

const markdown = `# Estructura del Proyecto (Re-cicla2)\n\n\`\`\`\n${tree}\`\`\`\n\n# Contenido de Archivos\n\n${files.join('\n---\n')}`;

// Guarda el archivo
fs.writeFileSync(path.join(__dirname, 'project_dump.md'), markdown);
console.log('\n==================================================');
console.log('✅ Contexto generado con éxito: project_dump.md');
console.log('==================================================');