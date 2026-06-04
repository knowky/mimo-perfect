# 实现商品服务（CRUD/搜索/分类）

**任务**: 分布式电商系统完整实现
**时间**: 2026-06-05T00:59:04.226087

# 分布式电商系统 - 商品服务实现

我将为您实现一个完整的分布式电商系统商品服务，包含CRUD、搜索和分类功能。

## 目录结构

```
/product-service
├── src/
│   ├── main/
│   │   ├── java/com/example/productservice/
│   │   │   ├── ProductServiceApplication.java
│   │   │   ├── config/
│   │   │   │   ├── ElasticsearchConfig.java
│   │   │   │   ├── RedisConfig.java
│   │   │   │   └── SwaggerConfig.java
│   │   │   ├── controller/
│   │   │   │   ├── ProductController.java
│   │   │   │   └── CategoryController.java
│   │   │   ├── service/
│   │   │   │   ├── ProductService.java
│   │   │   │   ├── ProductServiceImpl.java
│   │   │   │   ├── CategoryService.java
│   │   │   │   └── CategoryServiceImpl.java
│   │   │   ├── repository/
│   │   │   │   ├── ProductRepository.java
│   │   │   │   └── CategoryRepository.java
│   │   │   ├── search/
│   │   │   │   ├── ProductSearchRepository.java
│   │   │   │   └── ProductDocument.java
│   │   │   ├── entity/
│   │   │   │   ├── Product.java
│   │   │   │   └── Category.java
│   │   │   ├── dto/
│   │   │   │   ├── ProductDTO.java
│   │   │   │   ├── CategoryDTO.java
│   │   │   │   └── ProductSearchDTO.java
│   │   │   ├── exception/
│   │   │   │   ├── GlobalExceptionHandler.java
│   │   │   │   └── ProductNotFoundException.java
│   │   │   └── util/
│   │   │       ├── CacheUtil.java
│   │   │       └── DateUtil.java
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── application-dev.yml
│   │       ├── application-prod.yml
│   │       └── schema.sql
│   └── test/
│       └── java/com/example/productservice/
│           ├── ProductServiceApplicationTests.java
│           ├── ProductServiceTest.java
│           └── ProductControllerTest.java
├── pom.xml
└── README.md
```

## 1. 核心实体类

### Product.java - 商品实体
```java
package com.example.productservice.entity;

import lombok.Data;
import javax.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "products")
public class Product {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String name;
    
    @Column(length = 1000)
    private String description;
    
    @Column(nullable = false)
    private BigDecimal price;
    
    @Column(nullable = false)
    private Integer stock;
    
    @Column(name = "category_id")
    private Long categoryId;
    
    private String brand;
    
    private String model;
    
    @Column(name = "main_image")
    private String mainImage;
    
    @ElementCollection
    @CollectionTable(name = "product_images", joinColumns = @JoinColumn(name = "product_id"))
    @Column(name = "image_url")
    private List<String> images;
    
    @Column(name = "status")
    @Enumerated(EnumType.STRING)
    private ProductStatus status;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id", insertable = false, updatable = false)
    private Category category;
    
    public enum ProductStatus {
        ACTIVE, INACTIVE, OUT_OF_STOCK
    }
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
        if (status == null) {
            status = ProductStatus.ACTIVE;
        }
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
```

### Category.java - 分类实体
```java
package com.example.productservice.entity;

import lombok.Data;
import javax.persistence.*;
import java.time.LocalDateTime;
import java.util.List;

@Data
@Entity
@Table(name = "categories")
public class Category {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String name;
    
    private String description;
    
    @Column(name = "parent_id")
    private Long parentId;
    
    @Column(name = "level")
    private Integer level;
    
    @Column(name = "sort_order")
    private Integer sortOrder;
    
    @Column(name = "icon_url")
    private String iconUrl;
    
    @Column(name = "is_active")
    private Boolean isActive;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "parent_id", insertable = false, updatable = false)
    private Category parent;
    
    @OneToMany(mappedBy = "parent", fetch = FetchType.LAZY)
    @OrderBy("sortOrder ASC")
    private List<Category> children;
    
    @OneToMany(mappedBy = "category", fetch = FetchType.LAZY)
    private List<Product> products;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
        if (isActive == null) {
            isActive = true;
        }
        if (sortOrder == null) {
            sortOrder = 0;
        }
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
```

## 2. DTO类

### ProductDTO.java
```java
package com.example.productservice.dto;

import lombok.Data;
import javax.validation.constraints.*;
import java.math.BigDecimal;
import java.util.List;

@Data
public class ProductDTO {
    
    @NotBlank(message = "商品名称不能为空")
    @Size(max = 200, message = "商品名称不能超过200个字符")
    private String name;
    
    @Size(max = 2000, message = "商品描述不能超过2000个字符")
    private String description;
    
    @NotNull(message = "价格不能为空")
    @DecimalMin(value = "0.01", message = "价格必须大于0")
    private BigDecimal price;
    
    @NotNull(message = "库存不能为空")
    @Min(value = 0, message = "库存不能为负数")
    private Integer stock;
    
    @NotNull(message = "分类ID不能为空")
    private Long categoryId;
    
    private String brand;
    
    private String model;
    
    private String mainImage;
    
    private List<String> images;
    
    private String status;
    
    // 用于更新操作的ID
    private Long id;
}
```

### CategoryDTO.java
```java
package com.example.productservice.dto;

import lombok.Data;
import javax.validation.constraints.*;

@Data
public class CategoryDTO {
    
    @NotBlank(message = "分类名称不能为空")
    @Size(max = 100, message = "分类名称不能超过100个字符")
    private String name;
    
    @Size(max = 500, message = "分类描述不能超过500个字符")
    private String description;
    
    private Long parentId;
    
    private Integer level;
    
    @Min(value = 0, message = "排序值不能为负数")
    private Integer sortOrder;
    
    private String iconUrl;
    
    private Boolean isActive;
    
    private Long id;
}
```

### ProductSearchDTO.java
```java
package com.example.productservice.dto;

import lombok.Data;
import java.math.BigDecimal;
import java.util.List;

@Data
public class ProductSearchDTO {
    
    private String keyword;
    
    private Long categoryId;
    
    private BigDecimal minPrice;
    
    private BigDecimal maxPrice;
    
    private String brand;
    
    private String status;
    
    private String sortBy = "createdAt";
    
    private String sortOrder = "desc";
    
    private Integer page = 0;
    
    private Integer size = 20;
    
    private List<String> brands;
    
    private List<Long> categoryIds;
}
```

## 3. Repository层

### ProductRepository.java
```java
package com.example.productservice.repository;

import com.example.productservice.entity.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.List;

@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {
    
    // 按分类查找商品
    Page<Product> findByCategoryId(Long categoryId, Pageable pageable);
    
    // 按状态查找商品
    Page<Product> findByStatus(Product.ProductStatus status, Pageable pageable);
    
    // 按价格范围查找
    Page<Product> findByPriceBetween(BigDecimal minPrice, BigDecimal maxPrice, Pageable pageable);
    
    // 按品牌查找
    Page<Product> findByBrand(String brand, Pageable pageable);
    
    // 关键词搜索（模糊匹配）
    @Query("SELECT p FROM Product p WHERE p.name LIKE %:keyword% OR p.description LIKE %:keyword% OR p.brand LIKE %:keyword%")
    Page<Product> searchByKeyword(@Param("keyword") String keyword, Pageable pageable);
    
    // 多条件组合搜索
    @Query("SELECT p FROM Product p WHERE " +
           "(:keyword IS NULL OR p.name LIKE %:keyword% OR p.description LIKE %:keyword%) " +
           "AND (:categoryId IS NULL OR p.categoryId = :categoryId) " +
           "AND (:minPrice IS NULL OR p.price >= :minPrice) " +
           "AND (:maxPrice IS NULL OR p.price <= :maxPrice) " +
           "AND (:brand IS NULL OR p.brand = :brand) " +
           "AND (:status IS NULL OR p.status = :status)")
    Page<Product> advancedSearch(
            @Param("keyword") String keyword,
            @Param("categoryId") Long categoryId,
            @Param("minPrice") BigDecimal minPrice,
            @Param("maxPrice") BigDecimal maxPrice,
            @Param("brand") String brand,
            @Param("status") Product.ProductStatus status,
            Pageable pageable);
    
    // 根据分类ID列表查找商品
    @Query("SELECT p FROM Product p WHERE p.categoryId IN :categoryIds")
    List<Product> findByCategoryIds(@Param("categoryIds") List<Long> categoryIds);
    
    // 统计商品数量
    long countByCategoryId(Long categoryId);
    
    // 统计有库存的商品数量
    @Query("SELECT COUNT(p) FROM Product p WHERE p.stock > 0")
    long countInStock();
}
```

### CategoryRepository.java
```java
package com.example.productservice.repository;

import com.example.productservice.entity.Category;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CategoryRepository extends JpaRepository<Category, Long> {
    
    // 查找所有根分类
    List<Category> findByParentIdIsNullOrderBySortOrderAsc();
    
    // 按父分类查找子分类
    List<Category> findByParentIdOrderBySortOrderAsc(Long parentId);
    
    // 按层级查找分类
    List<Category> findByLevelOrderBySortOrderAsc(Integer level);
    
    // 查找所有激活的分类
    List<Category> findByIsActiveTrueOrderBySortOrderAsc();
    
    // 按名称搜索分类
    @Query("SELECT c FROM Category c WHERE c.name LIKE %:keyword%")
    List<Category> searchByName(@Param("keyword") String keyword);
    
    // 获取分类树
    @Query("SELECT c FROM Category c LEFT JOIN FETCH c.children WHERE c.parentId IS NULL ORDER BY c.sortOrder ASC")
    List<Category> findCategoryTree();
    
    // 检查分类下是否有商品
    @Query("SELECT CASE WHEN COUNT(p) > 0 THEN true ELSE false END FROM Product p WHERE p.categoryId = :categoryId")
    boolean hasProducts(@Param("categoryId") Long categoryId);
}
```

## 4. Elasticsearch搜索配置

### ProductDocument.java - Elasticsearch文档
```java
package com.example.productservice.search;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.elasticsearch.annotations.Document;
import org.springframework.data.elasticsearch.annotations.Field;
import org.springframework.data.elasticsearch.annotations.FieldType;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Data
@Document(indexName = "products")
public class ProductDocument {
    
    @Id
    private String id;
    
    @Field(type = FieldType.Text, analyzer = "ik_max_word", searchAnalyzer = "ik_smart")
    private String name;
    
    @Field(type = FieldType.Text, analyzer = "ik_max_word", searchAnalyzer = "ik_smart")
    private String description;
    
    @Field(type = FieldType.Keyword)
    private String brand;
    
    @Field(type = FieldType.Keyword)
    private String model;
    
    @Field(type = FieldType.Double)
    private BigDecimal price;
    
    @Field(type = FieldType.Integer)
    private Integer stock;
    
    @Field(type = FieldType.Long)
    private Long categoryId;
    
    @Field(type = FieldType.Keyword)
    private String categoryName;
    
    @Field(type = FieldType.Keyword)
    private String status;
    
    @Field(type = FieldType.Keyword)
    private List<String> tags;
    
    @Field(type = FieldType.Date)
    private LocalDateTime createdAt;
    
    @Field(type = FieldType.Date)
    private LocalDateTime updatedAt;
    
    @Field(type = FieldType.Text, analyzer = "ik_max_word", searchAnalyzer = "ik_smart")
    private String searchText; // 合并搜索字段
}
```

### ProductSearchRepository.java
```java
package com.example.productservice.search;

import org.springframework.data.elasticsearch.repository.ElasticsearchRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ProductSearchRepository extends ElasticsearchRepository<ProductDocument, String> {
    
    // 根据关键词搜索
    List<ProductDocument> findByNameContainingOrDescriptionContaining(
            String name, String description);
    
    // 根据分类ID查找
    List<ProductDocument> findByCategoryId(Long categoryId);
    
    // 根据品牌查找
    List<ProductDocument> findByBrand(String brand);
    
    // 根据状态查找
    List<ProductDocument> findByStatus(String status);
    
    // 根据价格范围查找
    List<ProductDocument> findByPriceBetween(BigDecimal minPrice, BigDecimal maxPrice);
    
    // 高级搜索
    @Query("{\"bool\": {\"must\": [" +
           "{\"multi_match\": {\"query\": \"?0\", \"fields\": [\"name^2\", \"description\", \"brand\", \"searchText\"]}}," +
           "{\"match\": {\"status\": \"ACTIVE\"}}]}}")
    Page<ProductDocument> searchProducts(String keyword, Pageable pageable);
}
```

## 5. Service层

### ProductService.java - 商品服务接口
```java
package com.example.productservice.service;

import com.example.productservice.dto.ProductDTO;
import com.example.productservice.dto.ProductSearchDTO;
import com.example.productservice.entity.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.List;

public interface ProductService {
    
    // CRUD操作
    Product createProduct(ProductDTO productDTO);
    
    Product updateProduct(Long id, ProductDTO productDTO);
    
    void deleteProduct(Long id);
    
    Product getProductById(Long id);
    
    List<Product> getAllProducts();
    
    Page<Product> getProducts(Pageable pageable);
    
    // 分类相关
    List<Product> getProductsByCategory(Long categoryId);
    
    Page<Product> getProductsByCategory(Long categoryId, Pageable pageable);
    
    // 搜索功能
    Page<Product> searchProducts(String keyword, Pageable pageable);
    
    Page<Product> advancedSearch(ProductSearchDTO searchDTO, Pageable pageable);
    
    // 库存管理
    void updateStock(Long productId, int quantity);
    
    void reduceStock(Long productId, int quantity);
    
    void increaseStock(Long productId, int quantity);
    
    // 状态管理
    void activateProduct(Long id);
    
    void deactivateProduct(Long id);
    
    // 同步到Elasticsearch
    void syncProductToElasticsearch(Long productId);
    
    void syncAllProductsToElasticsearch();
    
    // 统计方法
    long countProducts();
    
    long countProductsByCategory(Long categoryId);
    
    long countInStockProducts();
}
```

### ProductServiceImpl.java - 商品服务实现
```java
package com.example.productservice.service;

import com.example.productservice.dto.ProductDTO;
import com.example.productservice.dto.ProductSearchDTO;
import com.example.productservice.entity.Product;
import com.example.productservice.exception.ProductNotFoundException;
import com.example.productservice.repository.ProductRepository;
import com.example.productservice.search.ProductDocument;
import com.example.productservice.search.ProductSearchRepository;
import com.example.productservice.util.CacheUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.CachePut;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class ProductServiceImpl implements ProductService {
    
    private final ProductRepository productRepository;
    private final ProductSearchRepository productSearchRepository;
    private final CacheUtil cacheUtil;
    
    @Override
    @Transactional
    @CachePut(value = "product", key = "#result.id")
    public Product createProduct(ProductDTO productDTO) {
        Product product = new Product();
        product.setName(productDTO.getName());
        product.setDescription(productDTO.getDescription());
        product.setPrice(productDTO.getPrice());
        product.setStock(productDTO.getStock());
        product.setCategoryId(productDTO.getCategoryId());
        product.setBrand(productDTO.getBrand());
        product.setModel(productDTO.getModel());
        product.setMainImage(productDTO.getMainImage());
        product.setImages(productDTO.getImages());
        
        if (productDTO.getStatus() != null) {
            product.setStatus(Product.ProductStatus.valueOf(productDTO.getStatus()));
        } else {
            product.setStatus(Product.ProductStatus.ACTIVE);
        }
        
        Product savedProduct = productRepository.save(product);
        
        // 同步到Elasticsearch
        syncProductToElasticsearch(savedProduct.getId());
        
        log.info("商品创建成功: {}", savedProduct.getId());
        return savedProduct;
    }
    
    @Override
    @Transactional
    @CachePut(value = "product", key = "#id")
    public Product updateProduct(Long id, ProductDTO productDTO) {
        Product existingProduct = productRepository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException("商品不存在: " + id));
        
        existingProduct.setName(productDTO.getName());
        existingProduct.setDescription(productDTO.getDescription());
        existingProduct.setPrice(productDTO.getPrice());
        existingProduct.setStock(productDTO.getStock());
        existingProduct.setCategoryId(productDTO.getCategoryId());
        existingProduct.setBrand(productDTO.getBrand());
        existingProduct.setModel(productDTO.getModel());
        existingProduct.setMainImage(productDTO.getMainImage());
        existingProduct.setImages(productDTO.getImages());
        
        if (productDTO.getStatus() != null) {
            existingProduct.setStatus(Product.ProductStatus.valueOf(productDTO.getStatus()));
        }
        
        Product updatedProduct = productRepository.save(existingProduct);
        
        // 同步到Elasticsearch
        syncProductToElasticsearch(updatedProduct.getId());
        
        log.info("商品更新成功: {}", updatedProduct.getId());
        return updatedProduct;
    }
    
    @Override
    @Transactional
    @CacheEvict(value = "product", key = "#id")
    public void deleteProduct(Long id) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException("商品不存在: " + id));
        
        productRepository.delete(product);
        
        // 从Elasticsearch删除
        productSearchRepository.deleteById(id.toString());
        
        log.info("商品删除成功: {}", id);
    }
    
    @Override
    @Cacheable(value = "product", key = "#id")
    public Product getProductById(Long id) {
        return productRepository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException("商品不存在: " + id));
    }
    
    @Override
    public List<Product> getAllProducts() {
        return productRepository.findAll();
    }
    
    @Override
    public Page<Product> getProducts(Pageable pageable) {
        return productRepository.findAll(pageable);
    }
    
    @Override
    public List<Product> getProductsByCategory(Long categoryId) {
        return productRepository.findByCategoryId(categoryId, Pageable.unpaged()).getContent();
    }
    
    @Override
    public Page<Product> getProductsByCategory(Long categoryId, Pageable pageable) {
        return productRepository.findByCategoryId(categoryId, pageable);
    }
    
    @Override
    public Page<Product> searchProducts(String keyword, Pageable pageable) {
        // 先从Elasticsearch搜索
        Page<ProductDocument> searchResults = productSearchRepository.searchProducts(keyword, pageable);
        
        // 获取商品ID列表
        List<Long> productIds = searchResults.getContent().stream()
                .map(doc -> Long.parseLong(doc.getId()))
                .collect(Collectors.toList());
        
        if (productIds.isEmpty()) {
            // 如果Elasticsearch没有结果，回退到数据库搜索
            return productRepository.searchByKeyword(keyword, pageable);
        }
        
        // 根据ID从数据库获取完整商品信息
        List<Product> products = productRepository.findAllById(productIds);
        
        // 保持原来的排序
        return new org.springframework.data.domain.PageImpl<>(
                products, pageable, searchResults.getTotalElements());
    }
    
    @Override
    public Page<Product> advancedSearch(ProductSearchDTO searchDTO, Pageable pageable) {
        Product.ProductStatus status = null;
        if (searchDTO.getStatus() != null) {
            status = Product.ProductStatus.valueOf(searchDTO.getStatus());
        }
        
        return productRepository.advancedSearch(
                searchDTO.getKeyword(),
                searchDTO.getCategoryId(),
                searchDTO.getMinPrice(),
                searchDTO.getMaxPrice(),
                searchDTO.getBrand(),
                status,
                pageable
        );
    }
    
    @Override
    @Transactional
    public void updateStock(Long productId, int quantity) {
        Product product = productRepository.findById(productId)
                .orElseThrow(() -> new ProductNotFoundException("商品不存在: " + productId));
        
        product.setStock(product.getStock() + quantity);
        if (product.getStock() < 0) {
            product.setStock(0);
        }
        
        // 更新状态
        if (product.getStock() == 0) {
            product.setStatus(Product.ProductStatus.OUT_OF_STOCK);
        } else if (product.getStatus() == Product.ProductStatus.OUT_OF_STOCK) {
            product.setStatus(Product.ProductStatus.ACTIVE);
        }
        
        productRepository.save(product);
        syncProductToElasticsearch(productId);
    }
    
    @Override
    @Transactional
    public void reduceStock(Long productId, int quantity) {
        updateStock(productId, -quantity);
    }
    
    @Override
    @Transactional
    public void increaseStock(Long productId, int quantity) {
        updateStock(productId, quantity);
    }
    
    @Override
    @Transactional
    @CachePut(value = "product", key = "#id")
    public void activateProduct(Long id) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException("商品不存在: " + id));
        
        product.setStatus(Product.ProductStatus.ACTIVE);
        productRepository.save(product);
        syncProductToElasticsearch(id);
    }
    
    @Override
    @Transactional
    @CachePut(value = "product", key = "#id")
    public void deactivateProduct(Long id) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException("商品不存在: " + id));
        
        product.setStatus(Product.ProductStatus.INACTIVE);
        productRepository.save(product);
        syncProductToElasticsearch(id);
    }
    
    @Override
    public void syncProductToElasticsearch(Long productId) {
        try {
            Product product = productRepository.findById(productId)
                    .orElseThrow(() -> new ProductNotFoundException("商品不存在: " + productId));
            
            ProductDocument document = convertToDocument(product);
            productSearchRepository.save(document);
            
            log.info("商品同步到Elasticsearch成功: {}", productId);
        } catch (Exception e) {
            log.error("商品同步到Elasticsearch失败: {}", productId, e);
        }
    }
    
    @Override
    public void syncAllProductsToElasticsearch() {
        log.info("开始同步所有商品到Elasticsearch...");
        List<Product> products = productRepository.findAll();
        
        for (Product product : products) {
            try {
                ProductDocument document = convertToDocument(product);
                productSearchRepository.save(document);
            } catch (Exception e) {
                log.error("同步商品失败: {}", product.getId(), e);
            }
        }
        
        log.info("所有商品同步完成，总数: {}", products.size());
    }
    
    @Override
    public long countProducts() {
        return productRepository.count();
    }
    
    @Override
    public long countProductsByCategory(Long categoryId) {
        return productRepository.countByCategoryId(categoryId);
    }
    
    @Override
    public long countInStockProducts() {
        return productRepository.countInStock();
    }
    
    private ProductDocument convertToDocument(Product product) {
        ProductDocument document = new ProductDocument();
        document.setId(product.getId().toString());
        document.setName(product.getName());
        document.setDescription(product.getDescription());
        document.setBrand(product.getBrand());
        document.setModel(product.getModel());
        document.setPrice(product.getPrice());
        document.setStock(product.getStock());
        document.setCategoryId(product.getCategoryId());
        document.setStatus(product.getStatus().name());
        document.setCreatedAt(product.getCreatedAt());
        document.setUpdatedAt(product.getUpdatedAt());
        
        // 构建搜索文本
        StringBuilder searchText = new StringBuilder();
        searchText.append(product.getName()).append(" ");
        if (product.getDescription() != null) {
            searchText.append(product.getDescription()).append(" ");
        }
        if (product.getBrand() != null) {
            searchText.append(product.getBrand()).append(" ");
        }
        document.setSearchText(searchText.toString());
        
        return document;
    }
}
```

### CategoryService.java - 分类服务接口
```java
package com.example.productservice.service;

import com.example.productservice.dto.CategoryDTO;
import com.example.productservice.entity.Category;

import java.util.List;

public interface CategoryService {
    
    Category createCategory(CategoryDTO categoryDTO);
    
    Category updateCategory(Long id, CategoryDTO categoryDTO);
    
    void deleteCategory(Long id);
    
    Category getCategoryById(Long id);
    
    List<Category> getAllCategories();
    
    List<Category> getRootCategories();
    
    List<Category> getCategoriesByParent(Long parentId);
    
    List<Category> getCategoryTree();
    
    List<Category> searchCategories(String keyword);
    
    void activateCategory(Long id);
    
    void deactivateCategory(Long id);
    
    boolean hasProducts(Long categoryId);
    
    List<Category> getCategoriesByLevel(Integer level);
}
```

### CategoryServiceImpl.java - 分类服务实现
```java
package com.example.productservice.service;

import com.example.productservice.dto.CategoryDTO;
import com.example.productservice.entity.Category;
import com.example.productservice.exception.ProductNotFoundException;
import com.example.productservice.repository.CategoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class CategoryServiceImpl implements CategoryService {
    
    private final CategoryRepository categoryRepository;
    
    @Override
    @Transactional
    public Category createCategory(CategoryDTO categoryDTO) {
        Category category = new Category();
        category.setName(categoryDTO.getName());
        category.setDescription(categoryDTO.getDescription());
        category.setParentId(categoryDTO.getParentId());
        category.setLevel(categoryDTO.getLevel());
        category.setSortOrder(categoryDTO.getSortOrder());
        category.setIconUrl(categoryDTO.getIconUrl());
        category.setIsActive(categoryDTO.getIsActive() != null ? categoryDTO.getIsActive() : true);
        
        // 计算层级
        if (category.getParentId() != null) {
            Category parent = categoryRepository.findById(category.getParentId())
                    .orElseThrow(() -> new ProductNotFoundException("父分类不存在: " + category.getParentId()));
            category.setLevel(parent.getLevel() + 1);
        } else {
            category.setLevel(1);
        }
        
        Category savedCategory = categoryRepository.save(category);
        log.info("分类创建成功: {}", savedCategory.getId());
        return savedCategory;
    }
    
    @Override
    @Transactional
    @CacheEvict(value = "category", key = "#id")
    public Category updateCategory(Long id, CategoryDTO categoryDTO) {
        Category existingCategory = categoryRepository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException("分类不存在: " + id));
        
        existingCategory.setName(categoryDTO.getName());
        existingCategory.setDescription(categoryDTO.getDescription());
        existingCategory.setParentId(categoryDTO.getParentId());
        existingCategory.setSortOrder(categoryDTO.getSortOrder());
        existingCategory.setIconUrl(categoryDTO.getIconUrl());
        
        if (categoryDTO.getIsActive() != null) {
            existingCategory.setIsActive(categoryDTO.getIsActive());
        }
        
        // 重新计算层级
        if (categoryDTO.getParentId() != null) {
            Category parent = categoryRepository.findById(categoryDTO.getParentId())
                    .orElseThrow(() -> new ProductNotFoundException("父分类不存在: " + categoryDTO.getParentId()));
            existingCategory.setLevel(parent.getLevel() + 1);
        } else {
            existingCategory.setLevel(1);
        }
        
        Category updatedCategory = categoryRepository.save(existingCategory);
        log.info("分类更新成功: {}", updatedCategory.getId());
        return updatedCategory;
    }
    
    @Override
    @Transactional
    @CacheEvict(value = "category", key = "#id")
    public void deleteCategory(Long id) {
        Category category = categoryRepository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException("分类不存在: " + id));
        
        // 检查是否有子分类
        List<Category> children = categoryRepository.findByParentIdOrderBySortOrderAsc(id);
        if (!children.isEmpty()) {
            throw new RuntimeException("该分类下存在子分类，无法删除");
        }
        
        // 检查是否有商品
        if (categoryRepository.hasProducts(id)) {
            throw new RuntimeException("该分类下存在商品，无法删除");
        }
        
        categoryRepository.delete(category);
        log.info("分类删除成功: {}", id);
    }
    
    @Override
    @Cacheable(value = "category", key = "#id")
    public Category getCategoryById(Long id) {
        return categoryRepository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException("分类不存在: " + id));
    }
    
    @Override
    @Cacheable(value = "categories")
    public List<Category> getAllCategories() {
        return categoryRepository.findAll();
    }
    
    @Override
    @Cacheable(value = "root_categories")
    public List<Category> getRootCategories() {
        return categoryRepository.findByParentIdIsNullOrderBySortOrderAsc();
    }
    
    @Override
    public List<Category> getCategoriesByParent(Long parentId) {
        return categoryRepository.findByParentIdOrderBySortOrderAsc(parentId);
    }
    
    @Override
    @Cacheable(value = "category_tree")
    public List<Category> getCategoryTree() {
        return categoryRepository.findCategoryTree();
    }
    
    @Override
    public List<Category> searchCategories(String keyword) {
        return categoryRepository.searchByName(keyword);
    }
    
    @Override
    @Transactional
    @CacheEvict(value = "category", key = "#id")
    public void activateCategory(Long id) {
        Category category = categoryRepository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException("分类不存在: " + id));
        
        category.setIsActive(true);
        categoryRepository.save(category);
        log.info("分类激活成功: {}", id);
    }
    
    @Override
    @Transactional
    @CacheEvict(value = "category", key = "#id")
    public void deactivateCategory(Long id) {
        Category category = categoryRepository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException("分类不存在: " + id));
        
        category.setIsActive(false);
        categoryRepository.save(category);
        log.info("分类停用成功: {}", id);
    }
    
    @Override
    public boolean hasProducts(Long categoryId) {
        return categoryRepository.hasProducts(categoryId);
    }
    
    @Override
    @Cacheable(value = "categories_by_level", key = "#level")
    public List<Category> getCategoriesByLevel(Integer level) {
        return categoryRepository.findByLevelOrderBySortOrderAsc(level);
    }
}
```

## 6. Controller层

### ProductController.java
```java
package com.example.productservice.controller;

import com.example.productservice.dto.ProductDTO;
import com.example.productservice.dto.ProductSearchDTO;
import com.example.productservice.entity.Product;
import com.example.productservice.service.ProductService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;

@RestController
@RequestMapping("/api/products")
@RequiredArgsConstructor
@Api(tags = "商品管理接口")
public class ProductController {
    
    private final ProductService productService;
    
    @PostMapping
    @ApiOperation("创建商品")
    public ResponseEntity<Product> createProduct(
            @ApiParam("商品信息") @Valid @RequestBody ProductDTO productDTO) {
        Product product = productService.createProduct(productDTO);
        return ResponseEntity.status(HttpStatus.CREATED).body(product);
    }
    
    @PutMapping("/{id}")
    @ApiOperation("更新商品")
    public ResponseEntity<Product> updateProduct(
            @ApiParam("商品ID") @PathVariable Long id,
            @Api