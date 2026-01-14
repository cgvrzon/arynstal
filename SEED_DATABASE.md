# 🌱 Seed Database - Datos de Prueba

Este documento explica cómo usar el comando `seed_database` para poblar la base de datos con datos de prueba.

## 📋 ¿Qué hace este comando?

Crea automáticamente:
- ✅ **5 Servicios** (Aerotermia, Aire Acondicionado, Domótica KNX, etc.)
- ✅ **3 Usuarios** (1 oficina + 2 técnicos)
- ✅ **5 Leads** con diferentes estados
- ✅ **1 Presupuesto** de ejemplo
- ✅ **3 Mensajes de contacto**

## 🚀 Uso básico

### Crear todos los datos de prueba
```bash
python manage.py seed_database
```

### Limpiar datos existentes y crear nuevos
```bash
python manage.py seed_database --clear
```

## 🎯 Opciones avanzadas

### Solo crear servicios
```bash
python manage.py seed_database --only-services
```

### Solo crear leads
```bash
python manage.py seed_database --only-leads
```

### Solo crear usuarios
```bash
python manage.py seed_database --only-users
```

### Solo crear mensajes de contacto
```bash
python manage.py seed_database --only-contacts
```

## 👥 Usuarios creados

| Usuario | Password | Rol | Email |
|---------|----------|-----|-------|
| `admin` | `admin123` | Administrador | admin@arynstal.com |
| `maria_oficina` | `maria123` | Oficina | maria@arynstal.com |
| `carlos_tecnico` | `carlos123` | Técnico | carlos@arynstal.com |
| `jorge_tecnico` | `jorge123` | Técnico | jorge@arynstal.com |

## 📦 Servicios creados

1. **Aerotermia** - Climatización eficiente
2. **Aire Acondicionado** - Instalación y mantenimiento
3. **Domótica KNX** - Control inteligente del hogar
4. **Instalaciones Eléctricas** - Instalaciones certificadas
5. **Reformas Integrales** - Reformas llave en mano

## 📋 Leads de ejemplo

- 🆕 **Juan Pérez** - Lead nuevo (Aerotermia)
- 📞 **María González** - Contactado (Aire Acondicionado)
- 💰 **Pedro Martínez** - Presupuestado (Domótica KNX) → Con presupuesto de 8.500€
- 🆕 **Ana Rodríguez** - Nuevo (Instalación eléctrica)
- ✅ **Luis Fernández** - Cerrado (Reparación AC urgente)

## 🔧 Modificar los datos

Edita el archivo:
```
web/management/commands/seed_database.py
```

Busca las secciones:
- `_create_services()` - Para modificar servicios
- `_create_users()` - Para modificar usuarios
- `_create_leads()` - Para modificar leads
- `_create_contact_messages()` - Para modificar mensajes

## ⚠️ Importante

- El flag `--clear` **elimina los datos existentes** excepto el superusuario admin
- Los datos se crean dentro de una **transacción** (all-or-nothing)
- Si un dato ya existe (mismo email/username), se salta y muestra un aviso ⚠

## 💡 Consejos

### Resetear completamente la base de datos
```bash
# 1. Eliminar base de datos
rm db.sqlite3

# 2. Recrear estructura
python manage.py migrate

# 3. Crear superusuario
python manage.py createsuperuser --username admin --email admin@arynstal.com

# 4. Poblar con datos de prueba
python manage.py seed_database
```

### Probar con datos limpios
```bash
python manage.py seed_database --clear
```

## 📝 Changelog

### v1.0 (14-01-2026)
- Creación inicial del comando
- Soporte para servicios, usuarios, leads y mensajes de contacto
- Flags: --clear, --only-services, --only-leads, --only-users, --only-contacts
