/**
 * =============================================================================
 * ARCHIVO: static/js/cookies.js
 * PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
 * AUTOR: @cgvrzon
 * =============================================================================
 *
 * DESCRIPCIÓN:
 *   Banner de consentimiento de cookies según RGPD.
 *   Muestra un banner en la primera visita y guarda la preferencia
 *   del usuario en localStorage.
 *
 * FUNCIONALIDADES:
 *   - Muestra banner si no hay preferencia guardada
 *   - Opciones: Aceptar todas / Solo necesarias
 *   - Guarda preferencia en localStorage
 *   - No muestra banner en siguientes visitas
 *
 * USO:
 *   Se carga automáticamente desde base.html
 *
 * =============================================================================
 */

(function() {
  'use strict';

  // -------------------------------------------------------------------------
  // CONFIGURACIÓN
  // -------------------------------------------------------------------------

  const COOKIE_CONSENT_KEY = 'arynstal_cookie_consent';
  const BANNER_ID = 'cookie-consent-banner';

  // -------------------------------------------------------------------------
  // FUNCIONES PRINCIPALES
  // -------------------------------------------------------------------------

  /**
   * Verifica si el usuario ya dio su consentimiento.
   * @returns {boolean} True si ya hay preferencia guardada.
   */
  function hasConsent() {
    return localStorage.getItem(COOKIE_CONSENT_KEY) !== null;
  }

  /**
   * Guarda la preferencia del usuario.
   * @param {string} value - 'accepted' o 'rejected'
   */
  function saveConsent(value) {
    localStorage.setItem(COOKIE_CONSENT_KEY, value);
  }

  /**
   * Oculta y elimina el banner.
   */
  function hideBanner() {
    const banner = document.getElementById(BANNER_ID);
    if (banner) {
      banner.style.opacity = '0';
      banner.style.transform = 'translateY(100%)';
      setTimeout(function() {
        banner.remove();
      }, 300);
    }
  }

  /**
   * Crea y muestra el banner de cookies.
   */
  function showBanner() {
    // Evitar duplicados
    if (document.getElementById(BANNER_ID)) {
      return;
    }

    // Crear el banner
    const banner = document.createElement('div');
    banner.id = BANNER_ID;
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Consentimiento de cookies');

    // Estilos del banner
    banner.style.cssText = `
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: linear-gradient(135deg, #1e3a5f 0%, #0D3B66 100%);
      color: white;
      padding: 1rem 1.5rem;
      box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
      z-index: 9999;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      font-family: system-ui, -apple-system, sans-serif;
      transition: opacity 0.3s ease, transform 0.3s ease;
      opacity: 0;
      transform: translateY(100%);
    `;

    // Contenido del banner
    banner.innerHTML = `
      <div style="flex: 1; min-width: 280px;">
        <p style="margin: 0; font-size: 0.95rem; line-height: 1.5;">
          Utilizamos cookies propias y de terceros para mejorar tu experiencia.
          Puedes aceptar todas las cookies o solo las necesarias.
          <a href="/cookies/" style="color: #93c5fd; text-decoration: underline;">
            Más información
          </a>
        </p>
      </div>
      <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
        <button id="cookie-reject" style="
          padding: 0.6rem 1.2rem;
          border: 2px solid white;
          background: transparent;
          color: white;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 600;
          font-size: 0.9rem;
          transition: all 0.2s ease;
        ">
          Solo necesarias
        </button>
        <button id="cookie-accept" style="
          padding: 0.6rem 1.2rem;
          border: none;
          background: #10B981;
          color: white;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 600;
          font-size: 0.9rem;
          transition: all 0.2s ease;
        ">
          Aceptar todas
        </button>
      </div>
    `;

    // Añadir al DOM
    document.body.appendChild(banner);

    // Animar entrada
    requestAnimationFrame(function() {
      banner.style.opacity = '1';
      banner.style.transform = 'translateY(0)';
    });

    // Event listeners
    document.getElementById('cookie-accept').addEventListener('click', function() {
      saveConsent('accepted');
      hideBanner();
    });

    document.getElementById('cookie-reject').addEventListener('click', function() {
      saveConsent('rejected');
      hideBanner();
    });

    // Hover effects
    var acceptBtn = document.getElementById('cookie-accept');
    var rejectBtn = document.getElementById('cookie-reject');

    acceptBtn.addEventListener('mouseenter', function() {
      this.style.background = '#059669';
    });
    acceptBtn.addEventListener('mouseleave', function() {
      this.style.background = '#10B981';
    });

    rejectBtn.addEventListener('mouseenter', function() {
      this.style.background = 'rgba(255, 255, 255, 0.1)';
    });
    rejectBtn.addEventListener('mouseleave', function() {
      this.style.background = 'transparent';
    });
  }

  // -------------------------------------------------------------------------
  // INICIALIZACIÓN
  // -------------------------------------------------------------------------

  /**
   * Inicializa el sistema de consentimiento de cookies.
   * Se ejecuta cuando el DOM está listo.
   */
  function init() {
    // Solo mostrar si no hay consentimiento previo
    if (!hasConsent()) {
      // Pequeño delay para mejor UX (evitar flash)
      setTimeout(showBanner, 500);
    }
  }

  // Ejecutar cuando el DOM esté listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
