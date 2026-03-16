import React, { useState, useEffect, useCallback } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Download, X, RefreshCw, ExternalLink, AlertCircle, CheckCircle } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || `${window.location.origin}/api`;

export function UpdateNotification() {
  const [updateInfo, setUpdateInfo] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [installing, setInstalling] = useState(false);
  const [error, setError] = useState(null);
  const [dismissed, setDismissed] = useState(false);
  const [checking, setChecking] = useState(false);

  const checkForUpdates = useCallback(async () => {
    setChecking(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/updates/check`);
      const data = await response.json();
      if (data.available && !dismissed) {
        setUpdateInfo(data);
      } else {
        setUpdateInfo(null);
      }
    } catch (error) {
      console.error('Erreur lors de la vérification des mises à jour:', error);
      setError('Impossible de vérifier les mises à jour');
    } finally {
      setChecking(false);
    }
  }, [dismissed]);

  useEffect(() => {
    checkForUpdates();
    // Vérifier toutes les heures
    const interval = setInterval(checkForUpdates, 60 * 60 * 1000);
    return () => clearInterval(interval);
  }, [checkForUpdates]);

  const handleDownload = async () => {
    setDownloading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/updates/download`, {
        method: 'POST',
      });
      const data = await response.json();
      
      if (data.success) {
        setInstalling(true);
        // Attendre un peu pour que l'installation se termine
        setTimeout(() => {
          const msg = data.message || 'Mise a jour installee avec succes.';
          alert(`[SUCCESS] ${msg}`);
          setUpdateInfo(null);
          setDownloading(false);
          setInstalling(false);
        }, 1200);
      } else {
        setError(data.error || 'Erreur lors de la mise à jour');
        setDownloading(false);
      }
    } catch (error) {
      setError('Erreur lors de la mise à jour: ' + error.message);
      setDownloading(false);
    }
  };

  const handleDismiss = () => {
    setDismissed(true);
    setUpdateInfo(null);
    // Réinitialiser après 24h
    setTimeout(() => setDismissed(false), 24 * 60 * 60 * 1000);
  };

  if (dismissed || !updateInfo) return null;

  return (
    <Card className="mb-4 border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-lg text-blue-900">
              Nouvelle version disponible
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-blue-100 text-blue-700 border-blue-300">
                v{updateInfo.latest_version}
              </Badge>
              {updateInfo.prerelease && (
                <Badge variant="outline" className="bg-orange-100 text-orange-700 border-orange-300 text-xs">
                  Build automatique
                </Badge>
              )}
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDismiss}
            className="h-6 w-6 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription className="text-blue-700">
          Version actuelle : <span className="font-semibold">v{updateInfo.current_version}</span>
          {' → '}
          Version disponible : <span className="font-semibold">v{updateInfo.latest_version}</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}
        
        {installing ? (
          <div className="flex items-center gap-2 text-green-700">
            <CheckCircle className="h-5 w-5" />
            <span className="font-medium">Mise à jour installée ! Redémarrez l'application.</span>
          </div>
        ) : (
          <div className="flex flex-col sm:flex-row gap-2">
            <Button
              onClick={handleDownload}
              disabled={downloading || checking}
              className="bg-blue-600 hover:bg-blue-700 text-white flex-1"
            >
              {downloading ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Téléchargement...
                </>
              ) : installing ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Installation...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Mettre à jour maintenant
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={() => window.open(updateInfo.release_url, '_blank')}
              className="flex-1"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Voir les détails
            </Button>
          </div>
        )}
        
        {updateInfo.release_notes && (
          <details className="mt-3">
            <summary className="text-sm text-blue-600 cursor-pointer hover:text-blue-800">
              Notes de version
            </summary>
            <div className="mt-2 p-2 bg-white rounded text-sm text-gray-700 whitespace-pre-wrap">
              {updateInfo.release_notes.substring(0, 500)}
              {updateInfo.release_notes.length > 500 && '...'}
            </div>
          </details>
        )}
      </CardContent>
    </Card>
  );
}

