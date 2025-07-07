"""
Утилиты для работы с файлами
"""

import pandas as pd
import streamlit as st
from typing import Dict, Any, Optional
import io

def validate_file(uploaded_file) -> Dict[str, Any]:
    """
    Валидация загруженного файла
    
    Args:
        uploaded_file: Объект файла Streamlit
        
    Returns:
        Словарь с результатами валидации
    """
    
    validation_result = {
        'valid': False,
        'errors': [],
        'warnings': [],
        'rows': 0,
        'size_mb': 0
    }
    
    try:
        # Проверка размера файла
        file_size_mb = uploaded_file.size / (1024 * 1024)
        validation_result['size_mb'] = file_size_mb
        
        if file_size_mb > 10:
            validation_result['errors'].append(
                f"Файл слишком большой ({file_size_mb:.1f} MB). Максимальный размер: 10 MB"
            )
        
        # Проверка типа файла
        allowed_types = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
            'application/vnd.ms-excel',  # .xls
            'text/csv',  # .csv
            'application/csv'  # .csv alternative
        ]
        
        if uploaded_file.type not in allowed_types:
            validation_result['errors'].append(
                f"Неподдерживаемый тип файла: {uploaded_file.type}. "
                f"Поддерживаются: Excel (.xlsx, .xls), CSV (.csv)"
            )
        
        # Попытка прочитать файл для проверки содержимого
        try:
            df = get_file_preview(uploaded_file)
            
            if df is not None and not df.empty:
                rows_count = len(df)
                validation_result['rows'] = rows_count
                
                # Проверка количества строк
                if rows_count > 1000:
                    validation_result['errors'].append(
                        f"Слишком много строк ({rows_count}). Максимум: 1000 строк"
                    )
                elif rows_count < 1:
                    validation_result['errors'].append("Файл не содержит данных")
                elif rows_count < 5:
                    validation_result['warnings'].append(
                        f"Файл содержит очень мало данных ({rows_count} строк)"
                    )
                
                # Проверка наличия колонок
                if df.columns.empty:
                    validation_result['errors'].append("Файл не содержит колонок")
                elif len(df.columns) < 3:
                    validation_result['warnings'].append(
                        f"Файл содержит мало колонок ({len(df.columns)}). "
                        f"Рекомендуется минимум 3: название, количество, единица измерения"
                    )
            
            else:
                validation_result['errors'].append("Не удалось прочитать содержимое файла")
        
        except Exception as e:
            validation_result['errors'].append(f"Ошибка при чтении файла: {str(e)}")
        
        # Если нет критических ошибок, файл валиден
        validation_result['valid'] = len(validation_result['errors']) == 0
        
    except Exception as e:
        validation_result['errors'].append(f"Неожиданная ошибка валидации: {str(e)}")
    
    return validation_result

def get_file_preview(uploaded_file, max_rows: int = 50) -> Optional[pd.DataFrame]:
    """
    Получение предварительного просмотра файла
    
    Args:
        uploaded_file: Объект файла Streamlit
        max_rows: Максимальное количество строк для чтения
        
    Returns:
        DataFrame с данными или None при ошибке
    """
    
    try:
        # Сбрасываем указатель файла в начало
        uploaded_file.seek(0)
        
        # Определяем тип файла и читаем соответствующим образом
        if uploaded_file.type in [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel'
        ]:
            # Excel файлы
            df = pd.read_excel(uploaded_file, nrows=max_rows)
            
        elif uploaded_file.type in ['text/csv', 'application/csv']:
            # CSV файлы
            # Пробуем разные кодировки
            for encoding in ['utf-8', 'cp1251', 'windows-1251', 'iso-8859-1']:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding, nrows=max_rows)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # Если все кодировки не сработали
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='utf-8', errors='ignore', nrows=max_rows)
        
        else:
            return None
        
        # Очистка данных
        df = clean_dataframe(df)
        
        return df
    
    except Exception as e:
        st.error(f"Ошибка при чтении файла: {e}")
        return None

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Очистка DataFrame от пустых строк и колонок
    
    Args:
        df: Исходный DataFrame
        
    Returns:
        Очищенный DataFrame
    """
    
    # Удаляем полностью пустые строки
    df = df.dropna(how='all')
    
    # Удаляем полностью пустые колонки
    df = df.dropna(axis=1, how='all')
    
    # Убираем лишние пробелы в названиях колонок
    df.columns = df.columns.astype(str).str.strip()
    
    # Заменяем NaN в строковых колонках на пустые строки
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].fillna('').astype(str).str.strip()
    
    return df

def parse_excel(uploaded_file) -> Optional[pd.DataFrame]:
    """
    Парсинг Excel файла
    
    Args:
        uploaded_file: Объект файла Streamlit
        
    Returns:
        DataFrame с данными или None при ошибке
    """
    
    try:
        uploaded_file.seek(0)
        df = pd.read_excel(uploaded_file)
        return clean_dataframe(df)
    except Exception as e:
        st.error(f"Ошибка при чтении Excel файла: {e}")
        return None

def parse_csv(uploaded_file) -> Optional[pd.DataFrame]:
    """
    Парсинг CSV файла с автоопределением кодировки
    
    Args:
        uploaded_file: Объект файла Streamlit
        
    Returns:
        DataFrame с данными или None при ошибке
    """
    
    encodings_to_try = ['utf-8', 'cp1251', 'windows-1251', 'iso-8859-1']
    
    for encoding in encodings_to_try:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=encoding)
            return clean_dataframe(df)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            st.error(f"Ошибка при чтении CSV файла: {e}")
            return None
    
    # Если все кодировки не сработали, используем игнорирование ошибок
    try:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='utf-8', errors='ignore')
        st.warning("Файл прочитан с игнорированием некоторых символов")
        return clean_dataframe(df)
    except Exception as e:
        st.error(f"Критическая ошибка при чтении CSV файла: {e}")
        return None

def detect_file_encoding(uploaded_file) -> str:
    """
    Определение кодировки файла
    
    Args:
        uploaded_file: Объект файла Streamlit
        
    Returns:
        Название кодировки
    """
    
    try:
        import chardet
        
        uploaded_file.seek(0)
        raw_data = uploaded_file.read()
        result = chardet.detect(raw_data)
        uploaded_file.seek(0)
        
        return result.get('encoding', 'utf-8')
    except ImportError:
        # Если chardet не установлен, возвращаем utf-8 по умолчанию
        return 'utf-8'
    except Exception:
        return 'utf-8'

def get_file_info(uploaded_file) -> Dict[str, Any]:
    """
    Получение информации о файле
    
    Args:
        uploaded_file: Объект файла Streamlit
        
    Returns:
        Словарь с информацией о файле
    """
    
    info = {
        'name': uploaded_file.name,
        'size': uploaded_file.size,
        'size_mb': uploaded_file.size / (1024 * 1024),
        'type': uploaded_file.type,
        'encoding': 'unknown'
    }
    
    # Определяем кодировку для текстовых файлов
    if uploaded_file.type in ['text/csv', 'application/csv']:
        info['encoding'] = detect_file_encoding(uploaded_file)
    
    return info 